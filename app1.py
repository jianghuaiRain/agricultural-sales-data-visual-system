from flask import Flask,request,render_template,session,redirect,jsonify,make_response
import pandas as pd
import json
from utils1 import query
# 导入 utils1 包内 getHomeData.py 里的所有内容
from datetime import timedelta
from utils1.getHomeData import *

# 如果需要导入 utils1/utils.py 里的函数
from utils1.utils import get_merged_data, get_all_product_count
import numpy as np

app = Flask(__name__)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.secret_key = 'this is session_key you know'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

@app.after_request
def add_no_cache_headers(resp):
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp
    #禁止浏览器缓存

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if session.get('email'):
            return redirect('/home')
        # 获取所有记住的账号
        user_accounts_str = request.cookies.get('user_accounts', '{}')
        try:
            user_accounts = json.loads(user_accounts_str)
        except:
            user_accounts = {}
        
        # 默认回填最后一个记住的邮箱
        remembered_email = request.cookies.get('remember_email', '')
        remembered_password = user_accounts.get(remembered_email, '')
        
        return render_template('login.html', 
                             remembered_email=remembered_email, 
                             remembered_password=remembered_password,
                             user_accounts=json.dumps(user_accounts))
    elif request.method == 'POST':
        request.form = dict(request.form)
        email = request.form['email']
        password = request.form['password']
        
        def filter_fn(item):
            return email in item and password in item

        users = query.querys('select * from user', [], 'select')
        filter_user = list(filter(filter_fn, users))
        
        if len(filter_user):
            session['email'] = email
            remember = request.form.get('remember')
            session.permanent = False
            resp = make_response(redirect('/home'))
            
            # 获取现有记住的账号
            user_accounts_str = request.cookies.get('user_accounts', '{}')
            try:
                user_accounts = json.loads(user_accounts_str)
            except:
                user_accounts = {}

            if remember:
                # 记住当前账号密码，更新到字典中
                user_accounts[email] = password
                resp.set_cookie('remember_email', email, max_age=30*24*3600, samesite='Lax')
            else:
                # 如果取消“记住我”，从字典中移除当前账号
                if email in user_accounts:
                    del user_accounts[email]
                # 如果当前回显的邮箱被删了，也清掉 remember_email cookie
                if request.cookies.get('remember_email') == email:
                    resp.delete_cookie('remember_email')

            # 统一保存更新后的账号字典
            resp.set_cookie('user_accounts', json.dumps(user_accounts), max_age=30*24*3600, samesite='Lax')
            return resp
        else:
            return render_template(
                'login.html',
                remembered_email=email,
                error='密码错误',
                user_accounts=request.cookies.get('user_accounts', '{}')
            )


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        request.form = dict(request.form)
        print(request.form)
        if request.form['password'] != request.form['passwordChecked']:
            return render_template('register.html', error='两次输入的密码不一致', email=request.form.get('email',''))
        def filter_fn(item):
            return request.form['email'] in item


        users = query.querys('select * from user', [], 'select')
        filter_list = list(filter(filter_fn, users))
        if len(filter_list):
            return render_template('register.html', error='该账号已注册', email=request.form.get('email',''))
        else:
            query.querys('insert into user(email,password) values(%s,%s)', [request.form['email'], request.form['password']])

            return redirect('/login')




@app.route('/home',methods=['GET','POST'])
def home():
    email = session.get('email')
    if not email:
        return redirect('/login')
    home_data = getHomeData()
    return render_template(
        'index.html',
        email=email,
        home_data=home_data

                          )
@app.route('/logout')
def logout():
    # 只清除登录状态（session），保留记住密码的 Cookie
    session.clear()
    # 直接跳转，不删除 remember_email 和 remember_pwd！
    resp = make_response(redirect('/login'))
    return resp

@app.route('/api/home-data')
def api_home_data():
    data = getHomeData()
    if isinstance(data, dict):
        return jsonify(data)
    return jsonify({"error": data})

@app.route('/api/top-products')
def api_top_products():
    limit = request.args.get('limit', 10, type=int)
    df = get_merged_data()
    if df.empty:
        return jsonify([])
    df = df[df["quantity_value"] > 0]
    s = df.groupby("prod_product_name")["quantity_value"].sum().sort_values(ascending=False).head(limit)
    data = [{"name": k, "value": int(v)} for k, v in s.items()]
    return jsonify(data)

@app.route('/api/top-categories')
def api_top_categories():
    limit = request.args.get('limit', 10, type=int)
    df = get_merged_data()
    if df.empty:
        return jsonify([])
    df = df[df["quantity_value"] > 0]
    s = df.groupby("cate_category_name")["quantity_value"].sum().sort_values(ascending=False).head(limit)
    data = [{"name": k, "value": int(v)} for k, v in s.items()]
    return jsonify(data)

@app.route('/api/category-share')
def api_category_share():
    df = get_merged_data()
    if df.empty:
        return jsonify([])
    df = df[df["quantity_value"] > 0]
    s = df.groupby("cate_sub_category_name")["quantity_value"].sum().sort_values(ascending=False)
    total = int(s.sum()) if int(s.sum()) != 0 else 1
    data = [{"name": k, "value": int(v), "ratio": round(int(v) / total * 100, 2)} for k, v in s.items()]
    return jsonify(data)

@app.route('/api/region-sales')
def api_region_sales():
    limit = request.args.get('limit', 10, type=int)
    df = get_merged_data()
    if df.empty:
        return jsonify([])
    df = df[df["quantity_value"] > 0]
    s = df.groupby("city")["quantity_value"].sum().sort_values(ascending=False).head(limit)
    data = [{"name": k, "value": int(v)} for k, v in s.items()]
    return jsonify(data)

@app.route('/api/daily-heatmap')
def api_daily_heatmap():
    year = request.args.get('year', None, type=int)
    df = get_merged_data()
    if df.empty:
        return jsonify([])
    # 更健壮的时间列识别：支持英文与中文命名
    col_names = [str(c) for c in df.columns]
    date_cols = []
    for c in col_names:
        cl = c.lower()
        if ("date" in cl) or ("time" in cl) or ("created_at" in cl) or ("order" in cl and "date" in cl) or ("pay" in cl and "time" in cl) \
           or ("日期" in c) or ("时间" in c) or ("交易时间" in c) or ("下单时间" in c) or ("成交时间" in c):
            date_cols.append(c)
    if not date_cols:
        return jsonify([])
    dcol = date_cols[0]
    s = df.copy()
    # 转换数量为数值，过滤无效
    s["quantity_value"] = pd.to_numeric(s.get("quantity_value"), errors="coerce").fillna(0)
    # 解析日期
    s[dcol] = pd.to_datetime(s[dcol], errors="coerce")
    s = s.dropna(subset=[dcol])
    if year:
        s = s[s[dcol].dt.year == year]
    # 汇总到日期级别
    s["__day__"] = s[dcol].dt.date
    g = s.groupby("__day__")["quantity_value"].sum().sort_index()
    data = [{"date": str(k), "value": float(v)} for k, v in g.items()]
    return jsonify(data)

@app.route('/api/product-wordcloud')
def api_product_wordcloud():
    limit = request.args.get('limit', 120, type=int)
    df = get_merged_data()
    if df.empty:
        return jsonify([])
    invalid_names = {"无", "未知", "未知产品", ""}
    invalid_cates = {"无", "未知", "未知小类", "其他品类", ""}
    df_prod = df[~df.get("prod_product_name", "").isin(invalid_names)]
    series = df_prod["prod_product_name"].value_counts()
    if series.empty:
        df_cat = df[~df.get("cate_sub_category_name", "").isin(invalid_cates)]
        series = df_cat["cate_sub_category_name"].value_counts()
    series = series.head(limit)
    data = [{"name": str(k), "value": int(v)} for k, v in series.items() if str(k)]
    return jsonify(data)

@app.route('/api/top-subcategories')
def api_top_subcategories():
    limit = request.args.get('limit', 15, type=int)
    year = request.args.get('year', None, type=int)
    df = get_merged_data()
    if df.empty:
        return jsonify([])
    # 过滤无效二级分类
    invalid_cates = {"无", "未知", "未知小类", "其他品类", ""}
    df = df[~df.get("cate_sub_category_name").isin(invalid_cates)]
    # 数量
    df["quantity_value"] = pd.to_numeric(df.get("quantity_value"), errors="coerce").fillna(0)
    # 如果指定年份，按交易时间过滤
    if year:
        col_names = [str(c) for c in df.columns]
        date_cols = []
        for c in col_names:
            cl = c.lower()
            if ("date" in cl) or ("time" in cl) or ("created_at" in cl) or ("order" in cl and "date" in cl) or ("pay" in cl and "time" in cl) \
               or ("日期" in c) or ("时间" in c) or ("交易时间" in c) or ("下单时间" in c) or ("成交时间" in c):
                date_cols.append(c)
        if date_cols:
            dcol = date_cols[0]
            s = df.copy()
            s[dcol] = pd.to_datetime(s[dcol], errors="coerce")
            s = s.dropna(subset=[dcol])
            s = s[s[dcol].dt.year == year]
            df = s
    series = df.groupby("cate_sub_category_name")["quantity_value"].sum().sort_values(ascending=False).head(limit)
    data = [{"name": str(k), "value": float(v)} for k, v in series.items()]
    return jsonify(data)

@app.route('/api/sales-trend')
def api_sales_trend():
    year = request.args.get('year', None, type=int)
    freq = request.args.get('freq', 'day')
    df = get_merged_data()
    if df.empty:
        return jsonify([])
    col_names = [str(c) for c in df.columns]
    date_cols = []
    for c in col_names:
        cl = c.lower()
        if ("date" in cl) or ("time" in cl) or ("created_at" in cl) or ("order" in cl and "date" in cl) or ("pay" in cl and "time" in cl) \
           or ("日期" in c) or ("时间" in c) or ("交易时间" in c) or ("下单时间" in c) or ("成交时间" in c):
            date_cols.append(c)
    if not date_cols:
        return jsonify([])
    dcol = date_cols[0]
    s = df.copy()
    s["quantity_value"] = pd.to_numeric(s.get("quantity_value"), errors="coerce").fillna(0)
    s[dcol] = pd.to_datetime(s[dcol], errors="coerce")
    s = s.dropna(subset=[dcol])
    if year:
        s = s[s[dcol].dt.year == year]
    s = s.set_index(dcol).sort_index()
    if freq == 'week':
        g = s["quantity_value"].resample("W-MON").sum()
        data = [{"label": k.strftime("%Y-%m-%d"), "value": float(v)} for k, v in g.items()]
    elif freq == 'month':
        g = s["quantity_value"].resample("MS").sum()
        data = [{"label": k.strftime("%Y-%m"), "value": float(v)} for k, v in g.items()]
    else:
        g = s["quantity_value"].resample("D").sum()
        data = [{"label": (k.date() if hasattr(k, 'date') else k), "value": float(v)} for k, v in g.items()]
    return jsonify(data)

@app.route('/api/category-sales-count')
def api_category_sales_count():
    df = get_merged_data()
    if df.empty:
        return jsonify([])
    df = df.copy()
    df["quantity_value"] = pd.to_numeric(df.get("quantity_value"), errors="coerce").fillna(0)
    invalid = {"无", "未知", "未知小类", "其他品类", ""}
    df = df[~df.get("cate_category_name").isin(invalid)]
    s = df.groupby("cate_category_name")["quantity_value"].sum().sort_values(ascending=False)
    data = [{"name": str(k), "value": float(v)} for k, v in s.items()]
    return jsonify(data)

@app.route('/api/category-share-pie')
def api_category_share_pie():
    df = get_merged_data()
    if df.empty:
        return jsonify([])
    df = df.copy()
    df["quantity_value"] = pd.to_numeric(df.get("quantity_value"), errors="coerce").fillna(0)
    invalid = {"无", "未知", "未知小类", "其他品类", ""}
    df = df[~df.get("cate_category_name").isin(invalid)]
    s = df.groupby("cate_category_name")["quantity_value"].sum().sort_values(ascending=False)
    total = float(s.sum()) if float(s.sum()) != 0 else 1.0
    data = [{"name": str(k), "value": float(v), "ratio": round(float(v)/total*100, 2)} for k, v in s.items()]
    return jsonify(data)

@app.route('/api/price-buckets')
def api_price_buckets():
    df = get_merged_data()
    if df.empty:
        return jsonify([])
    cols = [c for c in df.columns if any(x in str(c).lower() for x in ["min_price","lowest_price","price","单价","最低价","价格"])]
    if not cols:
        return jsonify([])
    df = df.copy()
    stacks = []
    for c in cols:
        stacks.append(pd.to_numeric(df[c], errors="coerce"))
    df["_min_price_"] = pd.concat(stacks, axis=1).min(axis=1, skipna=True)
    df = df.dropna(subset=["_min_price_"])
    if "prod_product_id" in df.columns:
        df = df.drop_duplicates(subset=["prod_product_id"])
    vals = df["_min_price_"].to_numpy()
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return jsonify([])
    vmax = float(np.max(vals))
    # 低价段保持精细：0-15(步长1)、15-50(步长5)、50-110(步长10)
    e1 = np.arange(0, 15 + 1, 1, dtype=float)
    e2 = np.arange(15, 50 + 5, 5, dtype=float)
    e3_pre = np.arange(50, 110 + 10, 10, dtype=float)  # 包含至110

    # 110元后自适应：根据尾部范围选择“好读”的整数步长（10/20/50/100/200/500...）
    start_tail = 110.0
    edges_list = [e1, e2[1:], e3_pre[1:]]
    if vmax > start_tail:
        tail_range = vmax - start_tail
        nice_steps = [10, 20, 50, 100, 200, 500, 1000]
        # 目标尾部桶数量在 [12, 25] 之间，更易读
        selected = nice_steps[-1]
        for s in nice_steps:
            bins_cnt = int(np.ceil(tail_range / s))
            if 12 <= bins_cnt <= 25:
                selected = s
                break
            # 若较小步长导致桶太多，则逐步放大，直到桶数不超过25
            if bins_cnt > 25:
                continue
            # 若桶数过少，也先记录，后续若无更合适则使用
            if bins_cnt < 12 and selected == nice_steps[-1]:
                selected = s
        # 与步长对齐到“整数边界”（如100、150、200...）
        start_aligned = np.floor(start_tail / selected) * selected
        end_aligned = np.ceil(vmax / selected) * selected
        e_tail = np.arange(start_aligned, end_aligned + selected, selected, dtype=float)
        # 保留至对齐点之前的精细边界，之后采用自适应边界
        # e3_pre 已覆盖到 110；如果对齐点为100等低于110，需要保留到该点
        if start_aligned > 50:
            e3_keep = np.arange(50, start_aligned + 10, 10, dtype=float)
            edges_list = [e1, e2[1:], e3_keep[1:]]
        else:
            edges_list = [e1, e2[1:]]  # 对齐点<=50时直接拼接
        edges_list.append(e_tail[1:])
        edges = np.unique(np.concatenate(edges_list))
    else:
        upper10 = int(np.ceil(max(vmax, 50.0) / 10.0) * 10)
        e3 = np.arange(50, upper10 + 10, 10, dtype=float)
        edges = np.unique(np.concatenate([e1, e2[1:], e3[1:]]))
    hist, bins = np.histogram(vals, bins=edges)
    mask = hist > 0
    left = bins[:-1][mask]
    right = bins[1:][mask]
    def fmt(v): return str(int(round(v)))
    labels = [f"{fmt(left[i])}-{fmt(right[i])}元" for i in range(len(left))]
    data = [{"bin": labels[i], "value": int(hist[mask][i])} for i in range(len(labels))]
    return jsonify(data)

@app.route('/api/region-map')
def api_region_map():
    level = request.args.get('level', 'province')  # province | city
    metric = request.args.get('metric', 'sales')   # sales | amount | topcat

    # 如果是主要品类统计，直接基于产品表和地区表计算
    if metric == 'topcat':
        try:
            from utils1.utils import get_product_table, get_region_table, get_category_table
        except Exception:
            from .utils1.utils import get_product_table, get_region_table, get_category_table  # fallback
        df_prod = get_product_table()
        df_reg = get_region_table()
        df_cat = get_category_table()
        if df_prod is None or df_prod.empty or df_reg is None or df_reg.empty:
            return jsonify([])
        # 列名识别
        rid_col = "prod_region_id" if "prod_region_id" in df_prod.columns else ("region_id" if "region_id" in df_prod.columns else None)
        cat_id_col = "prod_category_id" if "prod_category_id" in df_prod.columns else ("category_id" if "category_id" in df_prod.columns else None)
        if not rid_col or not cat_id_col:
            return jsonify([])
        # 映射省份名称
        reg_map = df_reg.set_index("region_id")[["province"]].to_dict().get("province", {})
        # 映射品类名称
        cat_map = df_cat.set_index("cate_category_id")[["cate_category_name"]].to_dict().get("cate_category_name", {})
        # 统计每省内各品类的出现次数
        df_tmp = df_prod[[rid_col, cat_id_col]].dropna()
        df_tmp["province"] = df_tmp[rid_col].map(reg_map)
        df_tmp["category"] = df_tmp[cat_id_col].map(cat_map)
        df_tmp = df_tmp.dropna(subset=["province", "category"])
        if df_tmp.empty:
            return jsonify([])
        grp = df_tmp.groupby(["province", "category"]).size().reset_index(name="count")
        # 对每省取出现次数最多的品类
        rows = []
        for prov, g in grp.groupby("province"):
            g2 = g.sort_values(by="count", ascending=False).iloc[0]
            rows.append({"name": prov, "value": int(g2["count"]), "cat": str(g2["category"])})
        return jsonify(rows)

    # 默认：销量或销售额
    df = get_merged_data()
    if df.empty:
        return jsonify([])
    s = df.copy()
    s["quantity_value"] = pd.to_numeric(s.get("quantity_value"), errors="coerce").fillna(0)

    # 处理金额
    if metric == 'amount':
        price_cols = [c for c in s.columns if any(x in str(c).lower() for x in ["min_price","lowest_price","price","单价","最低价","价格"])]
        if price_cols:
            stacks = [pd.to_numeric(s[c], errors="coerce") for c in price_cols]
            s["__unit_price__"] = pd.concat(stacks, axis=1).min(axis=1, skipna=True)
            s["__unit_price__"] = pd.to_numeric(s["__unit_price__"], errors="coerce")
            s["__amount__"] = s["quantity_value"] * s["__unit_price__"]
            s = s[~s["__amount__"].isna()]
        else:
            # 没有价格列则直接返回空数据，避免误显示0
            return jsonify([])

    invalid = {"无", "未知", "未知省份", "未知城市", "", None, pd.NA}
    def norm_province(p):
        name = str(p).strip()
        if not name or name in invalid: return None
        specials = {
            "北京":"北京市","天津":"天津市","上海":"上海市","重庆":"重庆市",
            "内蒙古":"内蒙古自治区","广西":"广西壮族自治区","宁夏":"宁夏回族自治区",
            "新疆":"新疆维吾尔自治区","西藏":"西藏自治区",
            "香港":"香港特别行政区","澳门":"澳门特别行政区","台湾":"台湾省"
        }
        for k,v in specials.items():
            if k in name: return v
        if name.endswith(("省","市","自治区","特别行政区")):
            return name
        return name + "省"

    if level == 'city':
        grp_col = "city"
        s = s[~s[grp_col].isin(invalid)]
    else:
        grp_col = "province"
        s = s[~s[grp_col].isin(invalid)]
        s[grp_col] = s[grp_col].map(norm_province)
        s = s.dropna(subset=[grp_col])

    if metric == 'amount':
        grouped = s.groupby(grp_col)["__amount__"].sum()
    else:
        grouped = s.groupby(grp_col)["quantity_value"].sum()

    data = [{"name": str(k), "value": float(v)} for k, v in grouped.items() if float(v) > 0]
    return jsonify(data)

@app.route('/api/custom-query-options')
def api_custom_query_options():
    df = get_merged_data()
    if df.empty:
        return jsonify({"categories": [], "subcategories": [], "provinces": [], "cities": [], "products": []})
    res = {
        "categories": sorted([x for x in df.get("cate_category_name", []).dropna().unique().tolist() if x and x not in ["未知大类"]]),
        "subcategories": sorted([x for x in df.get("cate_sub_category_name", []).dropna().unique().tolist() if x and x not in ["未知小类"]]),
        "provinces": sorted([x for x in df.get("province", []).dropna().unique().tolist() if x and x not in ["未知省份"]]),
        "cities": sorted([x for x in df.get("city", []).dropna().unique().tolist() if x and x not in ["未知城市"]]),
        "products": sorted([x for x in df.get("prod_product_name", []).dropna().unique().tolist() if x and x not in ["未知产品"]])[:300]
    }
    return jsonify(res)

@app.route('/api/cities-by-province')
def api_cities_by_province():
    province = request.args.get('province', '')
    df = get_merged_data()
    if df.empty:
        return jsonify([])
    if not province:
        # 如果省份为空，返回所有城市
        cities = sorted([x for x in df.get("city", []).dropna().unique().tolist() if x and x not in ["未知城市"]])
    else:
        # 过滤指定省份的城市
        cities = sorted([x for x in df[df["province"] == province].get("city", []).dropna().unique().tolist() if x and x not in ["未知城市"]])
    return jsonify(cities)

@app.route('/api/custom-query-data')
def api_custom_query_data():
    # 参数
    dimension = request.args.get('dimension', 'time')  # time/category/region/price/product
    metric = request.args.get('metric', 'sales')       # sales/amount
    gran = request.args.get('gran', 'month')           # for time: day/week/month
    start = request.args.get('start', None)
    end = request.args.get('end', None)
    cat = request.args.get('category', None)
    subcat = request.args.get('subcategory', None)
    province = request.args.get('province', None)
    city = request.args.get('city', None)
    product = request.args.get('product', None)
    pmin = request.args.get('pmin', None, type=float)
    pmax = request.args.get('pmax', None, type=float)
    limit = request.args.get('limit', 20, type=int)

    df = get_merged_data()
    if df.empty:
        return jsonify([])
    s = df.copy()
    # 时间列识别
    date_cols = [c for c in s.columns if any(k in str(c).lower() for k in ["date","time","created_at","下单","成交","交易","时间","日期"])]
    dcol = date_cols[0] if date_cols else None
    if dcol:
        s[dcol] = pd.to_datetime(s[dcol], errors="coerce")
        s = s.dropna(subset=[dcol])
        if start:
            try:
                s = s[s[dcol] >= pd.to_datetime(start)]
            except Exception:
                pass
        if end:
            try:
                s = s[s[dcol] <= pd.to_datetime(end)]
            except Exception:
                pass
    # 数量
    s["quantity_value"] = pd.to_numeric(s.get("quantity_value"), errors="coerce").fillna(0)
    # 价格过滤
    price_cols = [c for c in s.columns if any(x in str(c).lower() for x in ["min_price","lowest_price","price","单价","最低价","价格"])]
    if pmin is not None or pmax is not None:
        if price_cols:
            stacks = [pd.to_numeric(s[c], errors="coerce") for c in price_cols]
            s["__filter_price__"] = pd.concat(stacks, axis=1).min(axis=1, skipna=True)
            if pmin is not None:
                s = s[s["__filter_price__"] >= pmin]
            if pmax is not None:
                s = s[s["__filter_price__"] <= pmax]
    # 维度过滤
    if cat: s = s[s.get("cate_category_name").astype(str) == cat]
    if subcat: s = s[s.get("cate_sub_category_name").astype(str) == subcat]
    if province: s = s[s.get("province").astype(str) == province]
    if city: s = s[s.get("city").astype(str) == city]
    if product: s = s[s.get("prod_product_name").astype(str) == product]
    # 金额指标
    if metric == 'amount':
        if price_cols:
            stacks = [pd.to_numeric(s[c], errors="coerce") for c in price_cols]
            s["__unit_price__"] = pd.concat(stacks, axis=1).min(axis=1, skipna=True)
            s["__unit_price__"] = pd.to_numeric(s["__unit_price__"], errors="coerce")
            s["__metric__"] = s["quantity_value"] * s["__unit_price__"]
            s = s[~s["__metric__"].isna()]
        else:
            return jsonify([])
    else:
        s["__metric__"] = s["quantity_value"]

    # 分组聚合
    if dimension == 'time' and dcol:
        s = s.set_index(dcol).sort_index()
        if gran == 'day':
            g = s["__metric__"].resample("D").sum()
            data = [{"label": k.strftime("%Y-%m-%d"), "value": float(v)} for k, v in g.items()]
        elif gran == 'week':
            g = s["__metric__"].resample("W-MON").sum()
            data = [{"label": k.strftime("%Y-%m-%d"), "value": float(v)} for k, v in g.items()]
        else:
            g = s["__metric__"].resample("MS").sum()
            data = [{"label": k.strftime("%Y-%m"), "value": float(v)} for k, v in g.items()]
        return jsonify(data)
    elif dimension == 'category':
        g = s.groupby("cate_sub_category_name")["__metric__"].sum().sort_values(ascending=False).head(limit)
        return jsonify([{"label": str(k), "value": float(v)} for k, v in g.items()])
    elif dimension == 'region':
        g = s.groupby("province")["__metric__"].sum().sort_values(ascending=False).head(limit)
        return jsonify([{"label": str(k), "value": float(v)} for k, v in g.items()])
    elif dimension == 'product':
        g = s.groupby("prod_product_name")["__metric__"].sum().sort_values(ascending=False).head(limit)
        return jsonify([{"label": str(k), "value": float(v)} for k, v in g.items()])
    else:
        # 价格分段（默认 10 桶）
        vals = s["__metric__"]
        e = 10
        if price_cols:
            pstack = [pd.to_numeric(s[c], errors="coerce") for c in price_cols]
            pv = pd.concat(pstack, axis=1).min(axis=1, skipna=True).dropna().to_numpy()
            if pv.size > 0:
                vmax = float(np.max(pv))
                edges = np.linspace(0, np.ceil(vmax/10)*10, num=e+1)
                hist, bins = np.histogram(pv, bins=edges, weights=s.loc[pv.index if hasattr(pv,'index') else s.index, "__metric__"] if hasattr(pv,'index') else None)
                data = []
                for i in range(len(hist)):
                    left = int(bins[i]); right = int(bins[i+1])
                    data.append({"label": f"{left}-{right}元", "value": float(hist[i])})
                return jsonify(data)
        return jsonify([])

@app.route('/__info')
def info():
    import os, time
    tpl_paths = getattr(app.jinja_loader, 'searchpath', [])
    tpl_file = None
    mtime = None
    for p in tpl_paths:
        candidate = os.path.join(p, 'index.html')
        if os.path.exists(candidate):
            tpl_file = candidate
            mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(candidate)))
            break
    return jsonify({
        "template_searchpath": tpl_paths,
        "index_template_file": tpl_file,
        "index_template_mtime": mtime,
        "home_data_sample": getHomeData()
    })

@app.route('/')
def allRequest():
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
