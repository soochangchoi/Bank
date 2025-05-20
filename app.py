from flask import Flask, render_template, request, jsonify
import pandas as pd
import re

app = Flask(__name__)

# ✔ 예금/적금 데이터 로드
deposit_tier1 = pd.read_csv('예금_1금융권_포함.csv')
deposit_tier2 = pd.read_csv('예금_2금융권.csv')
savings_tier1 = pd.read_csv('적금_1금융권_포함.csv')
savings_tier2 = pd.read_csv('적금_2금융권.csv')

# ✔ 대출 데이터 클린 및 로드
def clean_loan_data(file):
    df = pd.read_csv(file)
    df = df.rename(columns=lambda x: x.strip())
    df = df.rename(columns={
        '금리': '기본금리(%)',
        '대출 금리': '기본금리(%)',
        '대출금리': '기본금리(%)',
        '한도': '대출한도',
        '상환 방식': '상환방식',
        '상환방식': '상환방식',
        '가입 대상': '가입대상',
        '가입대상': '가입대상',
        '가입방법': '가입방법',
        '만기이자': '만기이자',
        '저축기간(개월)': '저축기간(개월)',
    })
    required_cols = ['금융회사명', '상품명', '기본금리(%)', '대출한도', '상환방식', '가입대상', '저축기간(개월)', '만기이자']
    for col in required_cols:
        if col not in df.columns:
            df[col] = '정보 없음'
    df = df.dropna(subset=['금융회사명', '상품명'])
    df.fillna('정보 없음', inplace=True)
    return df

loan_files = ['햇살론_정리.csv', '소액비상금_대출_정리.csv', '새희망홀씨_대출_정리.csv', '무직자_대출_정리.csv', '사잇돌_대출_정리.csv']
loan_data = pd.concat([clean_loan_data(file) for file in loan_files])

# ✔ 금융용어사전 데이터 로드 및 초성 기준 생성
terms_df = pd.read_excel('통계용어사전.xlsx')

def get_initial_consonant(word):
    if not word:
        return ''
    first_char = word[0]
    if '가' <= first_char <= '힣':
        cho_list = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ',
                    'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
        char_code = ord(first_char) - ord('가')
        cho_index = int(char_code / 588)
        return cho_list[cho_index]
    elif re.match(r'[A-Za-z]', first_char):
        return 'A-Z'
    else:
        return first_char

terms_df['초성'] = terms_df['용어'].apply(get_initial_consonant)

# ✔ 홈
@app.route('/')
def home():
    return render_template('home_menu.html')

# ✔ 예금 라우트
@app.route('/deposits')
def deposits_page():
    periods = sorted(pd.concat([deposit_tier1, deposit_tier2])['저축기간(개월)'].unique())
    banks = {
        '1금융권': sorted(deposit_tier1['금융회사명'].unique()),
        '2금융권': sorted(deposit_tier2['금융회사명'].unique())
    }
    return render_template('filter_page.html', product_type='예금', product_type_url='deposits', periods=periods, banks=banks)

@app.route('/deposits/detail/<product_name>')
def deposits_detail(product_name):
    product = pd.concat([deposit_tier1, deposit_tier2])
    product = product[product['상품명'] == product_name].iloc[0]
    return render_template('product_detail.html', product=product, product_type='예금', product_type_url='deposits')

@app.route('/api/deposits')
def api_deposits():
    period = request.args.get('period')
    bank = request.args.get('bank')
    rate = float(request.args.get('rate', 0))

    data = pd.concat([deposit_tier1, deposit_tier2])
    if period:
        data = data[data['저축기간(개월)'] == int(period)]
    if bank:
        data = data[data['금융회사명'].str.contains(bank)]
    if rate:
        data = data[data['최고우대금리(%)'] >= rate]

    products = data.to_dict(orient='records')
    return jsonify({'products': products, 'total': len(products)})

# ✔ 적금 라우트
@app.route('/savings')
def savings_page():
    periods = sorted(pd.concat([savings_tier1, savings_tier2])['저축기간(개월)'].unique())
    banks = {
        '1금융권': sorted(savings_tier1['금융회사명'].unique()),
        '2금융권': sorted(savings_tier2['금융회사명'].unique())
    }
    return render_template('filter_page.html', product_type='적금', product_type_url='savings', periods=periods, banks=banks)

@app.route('/savings/detail/<product_name>')
def savings_detail(product_name):
    product = pd.concat([savings_tier1, savings_tier2])
    product = product[product['상품명'] == product_name].iloc[0]
    return render_template('product_detail.html', product=product, product_type='적금', product_type_url='savings')

@app.route('/api/savings')
def api_savings():
    period = request.args.get('period')
    bank = request.args.get('bank')
    rate = float(request.args.get('rate', 0))

    data = pd.concat([savings_tier1, savings_tier2])
    if period:
        data = data[data['저축기간(개월)'] == int(period)]
    if bank:
        data = data[data['금융회사명'].str.contains(bank)]
    if rate:
        data = data[data['최고우대금리(%)'] >= rate]

    products = data.to_dict(orient='records')
    return jsonify({'products': products, 'total': len(products)})

# ✔ 대출 라우트
@app.route('/loans')
def loans_page():
    products = loan_data.to_dict(orient='records')
    return render_template('loans_list.html', products=products)

@app.route('/loans/detail/<product_name>')
def loans_detail(product_name):
    product = loan_data[loan_data['상품명'] == product_name].iloc[0]
    return render_template('product_detail.html', product=product, product_type='대출', product_type_url='loans')

# ✔ 모아플러스 홈
@app.route('/plus')
def plus_home():
    return render_template('plus_home.html')

# ✔ 모아플러스 - 금융사전
@app.route('/plus/terms')
def terms_home():
    categories = sorted(terms_df['초성'].unique())
    return render_template('terms_home.html', categories=categories)

@app.route('/plus/terms/list/<initial>')
def terms_list(initial):
    filtered = terms_df[terms_df['초성'] == initial]
    terms = filtered[['용어', '설명']].sort_values('용어').to_dict(orient='records')
    return render_template('terms_list.html', category=initial, terms=terms)

@app.route('/plus/terms/detail/<term>')
def term_detail_direct(term):
    row = terms_df[terms_df['용어'] == term].iloc[0]
    return render_template('term_detail.html', term=row['용어'], description=row['설명'], category='검색결과')

@app.route('/plus/terms/search')
def search_terms():
    query = request.args.get('query', '').strip()
    filtered = terms_df[terms_df['용어'].str.contains(query)]
    terms = filtered[['용어', '설명']].sort_values('용어').to_dict(orient='records')
    return render_template('terms_list.html', category=f"검색결과: {query}", terms=terms)

# ✔ 모아플러스 - 청년정책
@app.route('/plus/youth')
def plus_youth_policy():
    return render_template('youth_policy.html')

if __name__ == '__main__':
    app.run(debug=True)
