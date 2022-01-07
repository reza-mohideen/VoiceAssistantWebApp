import yfinance as yf
import csv

def get_symbol(user_stock_inquiry: str) -> None:

    with open('../resources/symbols.csv', mode='r') as inp:
        reader = csv.reader(inp)
        stock_dict = {rows[0]: rows[1] for rows in reader}
    stock_lower_dict = {k.lower(): v for(k, v) in stock_dict.items()}

    extra_words = ['co.', 'corp.', 'communications', 'inc.', 'laboratories', 'ltd.', 'plc.', 'of', 'the']

    for key in stock_lower_dict:
        try:
            company_names = key.split(',')
            company_names[0] = key.replace('&', ' and ')
            for word in extra_words:
                if word in company_names[0]:
                    company_names[0] = company_names[0].replace(' ' + word, '')
            if company_names[0] in user_stock_inquiry.lower():
                return stock_lower_dict.get(key)
        except IndexError:
            continue

    return None


def company_stock(user_inquiry):
    ticker = get_symbol(user_inquiry.lower())
    if ticker != None:
        company = yf.Ticker(ticker)

        try:
            company_stock = {'name': company.info['shortName'],
                             'price': company.info['currentPrice'],
                             'recommendation': company.info['recommendationKey']}

            print(company.info['shortName'] + " (" + company.info['symbol'] + ")")
            print("Current Price: ", company.info['currentPrice'])
            print("Recommendation: ", company.info['recommendationKey'])
            return company_stock
        except KeyError:
            print("Company cannot be found.")

    else:
        print("The company symbol cannot be found.")
        return None


if __name__ == "__main__":
    company_stock("tell me about abbvie")  # stock that exists (works)
    company_stock("show me abbott stocks")  # stock that exists (works)
    company_stock("give me bob stock")  # stock that does not exist (works)
    company_stock("show me GOOGLE stock")  # stock that exists but all caps (works)
    company_stock("tell me the stock price of facebook")  # stock for a company with the word 'of' (works)
