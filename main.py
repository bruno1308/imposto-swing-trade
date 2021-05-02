import glob, os
import collections

startTitulo = "1-BOVESPA"
tipoTitulo = "C/V Tipo mercado"


def file_to_text(path):
    import io
    f = io.open(path, mode="r", encoding="utf-8")
    return f


def remove_exceeding_spaces(string):
    return " ".join(string.split())


def process_operation(line, titulos, qties, prices, optypes):
    split = line.split(' ');
    found_qty_index = -1
    for i in range(0, len(split)):
        if i == 1:
            optypes.append(split[i])
        if i == 3:
            titulos.append(split[i] + " " + split[i + 1])
        if i > 3 and is_number(split[i].replace('.', '')) and found_qty_index == -1:
            split[i] = split[i].replace('.', '')
            qties.append(split[i])
            found_qty_index = i
        if i == found_qty_index + 1 and found_qty_index >= 0:
            split[i] = split[i].replace(',', '.')
            prices.append(split[i])


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False


def print_month_result(month, current_balance, emolumentos, taxa_liquidacao, irrf, vendas_no_mes):
    print("----------- Balanço Final do Mês ------------")

    print("Mostrando resultados para o mês de " + month)
    print("Saldo Final do Mês = R$" + str(round(current_balance, 2)))
    print("Taxa de Liquidação do Mês = R$" + str(taxa_liquidacao))
    print("Emolumentos do Mês = R$" + str(emolumentos))
    print("I.R.R.F do Mês = R$" + str(irrf))

    balance_after_deduction = current_balance - taxa_liquidacao - emolumentos - irrf

    print("Saldo Final depois de descontos = R$" + str(round(balance_after_deduction, 2)))

    if vendas_no_mes < 20000:
        print("Vendas no mês de apenas R$" + str(vendas_no_mes) + " menor que R$20000, isento de imposto")
        print("--------------------------------------------------------------------")
        print("--------------------------------------------------------------------")
        print("--------------------------------------------------------------------")
        print("--------------------------------------------------------------------")
        return

    if balance_after_deduction > 0:
        print("Se apenas Swing Trade, você deve pagar = R$" + str(round(balance_after_deduction * 0.15, 2)) + " no mês " + month)
    else:
        print("Saldo negativo, nada a pagar no mês " + month)
    print("--------------------------------------------------------------------")
    print("--------------------------------------------------------------------")
    print("--------------------------------------------------------------------")
    print("--------------------------------------------------------------------")


def post_process(titulos, qties, prices, optypes, dates, taxa_liquidacao_by_month, emolumentos_by_month, irrf_by_month):
    titulo_to_info = {}
    month_to_current_balance = {}
    month_to_spend = {}
    last_month = dates[0][3:5]
    month = ''
    for i in range(0, len(titulos)):
        titulo = titulos[i]
        qty = int(qties[i])
        price = float(prices[i])
        optype = optypes[i]
        date = dates[i]
        month = date[3:5]

        if month != last_month:
            print_month_result(last_month, month_to_current_balance[last_month], emolumentos_by_month[last_month],
                               taxa_liquidacao_by_month[last_month], irrf_by_month[last_month],
                               month_to_spend[last_month])
            last_month = month
        if optype == 'C':
            if titulo in titulo_to_info:
                avg_price = titulo_to_info[titulo]["avgprice"]
                qty_so_far = titulo_to_info[titulo]["qty"]
                operation_spent = price * qty
                newAvg = (operation_spent + (avg_price * qty_so_far)) / (qty_so_far + qty)
                titulo_to_info[titulo]["avgprice"] = newAvg
                titulo_to_info[titulo]["qty"] = qty + qty_so_far
                continue
            else:
                titulo_to_info[titulo] = {}
                titulo_to_info[titulo]["avgprice"] = price
                titulo_to_info[titulo]["qty"] = qty
        elif optype == 'V':
            if titulo in titulo_to_info:
                avg_price = titulo_to_info[titulo]["avgprice"]
                qty_so_far = titulo_to_info[titulo]["qty"]
                balance = qty * (price - avg_price)
                if month not in month_to_spend:
                    month_to_spend[month] = 0
                month_to_spend[month] += price * qty
                if balance > 0:
                    print("Lucro vendendo " + titulo + " de R$ " + str(round(balance, 2)) + " em " + str(date))
                else:
                    print("Prejuizo vendendo " + titulo + " de R$ " + str(round(balance, 2)) + " em " + str(date))
                titulo_to_info[titulo]["qty"] = qty_so_far - qty
                if month not in month_to_current_balance:
                    month_to_current_balance[month] = 0
                month_to_current_balance[month] += balance
                continue
            else:
                print("Erro, vendendo " + titulo + " antes de comprar em " + str(date))
    print_month_result(month, month_to_current_balance[month], emolumentos_by_month[month], taxa_liquidacao_by_month[month],
                       irrf_by_month[month], month_to_spend[month])
    for key, value in list(titulo_to_info.items()):
        if titulo_to_info[key]['qty'] == 0:
            del titulo_to_info[key]
    ordered_titulo_to_info = collections.OrderedDict(sorted(titulo_to_info.items()))
    print(ordered_titulo_to_info)



if __name__ == "__main__":
    titulos = []
    qties = []
    prices = []
    optypes = []
    dates = []
    emolumentos_by_month = {}
    irrf_by_month = {}
    taxa_liquidacao_by_month = {}
    retval = os.getcwd()
    os.chdir(retval)
    for file in sorted(glob.glob("*.txt")):
        text = file_to_text(file)
        step = 0
        idx = 0
        lines = text.readlines()
        date = ''
        month = ''
        for line in lines:
            # print(line)
            if "1-BOVESPA" in line:
                process_operation(line, titulos, qties, prices, optypes)
            if "Data pregão" in line:
                date = lines[idx + 1].replace('\n', '')
                month = date[3:5]
                dates.append(date)
            if "Taxa de liquidação" in line:
                split = line.split(' ')
                k = 0
                while not is_number(split[k].replace(',', '.')):
                    k += 1
                    continue
                if month not in taxa_liquidacao_by_month:
                    taxa_liquidacao_by_month[month] = 0
                taxa_liquidacao_by_month[month] += float(split[k].replace(',', '.'))
            if "Emolumentos" in line:
                split = line.split(' ')
                k = 0
                while not is_number(split[k].replace(',', '.')):
                    k += 1
                    continue
                if month not in emolumentos_by_month:
                    emolumentos_by_month[month] = 0
                emolumentos_by_month[month] += float(split[k].replace(',', '.'))
            if "I.R.R.F." in line:
                split = line.split(' ')
                k = 0
                while not is_number(split[k].replace(',', '.')):
                    k += 1
                    continue
                if month not in irrf_by_month:
                    irrf_by_month[month] = 0
                irrf_by_month[month] += float(split[k].replace(',', '.'))
            idx += 1
        new_elements_number = len(optypes) - len(dates)
        for i in range(0, new_elements_number):
            dates.append(dates[len(dates) - 1])
        # print(titulos)
        # print(" LenT = " + str(len(titulos)))
        # print(qties)
        # print(" LenQ = " + str(len(qties)))
        # print(prices)
        # print(" LenP = " + str(len(prices)))
        # print(optypes)
        # print(" LenO = " + str(len(optypes)))
        # print(dates)
        # print(" LenD = " + str(len(dates)))
    post_process(titulos, qties, prices, optypes, dates, taxa_liquidacao_by_month, emolumentos_by_month, irrf_by_month)
    #
    #
