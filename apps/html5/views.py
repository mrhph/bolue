#!/use/bin/env python
# -*- coding: UTF-8 -*-# -*- coding: UTF-8 -*-

import requests
import json
import re
from datetime import datetime, timedelta
from apps import app
from flask import render_template, request, g
from apps.dbinstance import db
from apps.member.models import Member_pay_info, Member_real_info, Member, Member_invite_info
from apps.product.models import Borrow_attachment, Borrow_file, Product_image, Product_borrower_image, Product_info, Borrower_info, Account_info
from apps.utils import toolkit
from apps.utils.message import send_message
from apps.activity.utils import convertPhone, lc_red_pocket, add_integral_record
from apps.activity.views import check_activity
from apps.activity.models import Rank_list
from apps.rewards.models import Activity
from apps.asset.models import Member_red_pocket_type, Member_red_pocket
from apps.member.utils import do_register
from config import JAVA_BAOQUAN_URL, BOLUO_URL
from sqlalchemy import and_, or_, func
from apps.product.models import Invest_info
from apps.product.utils import cncurrency
from apps.html5.utils import htsort, creat_rank_list, create_format, send_pinapple, hide_some_fields


@app.route('/v1/html5/letter_of_authorization/<phone>/<product_name>')
def letter_of_authorization(phone,product_name):
    render_data = {}
    try:
        query_top = db.session.query(Member_pay_info,Member_real_info,Member.phone)
        query = query_top.filter(Member.phone==phone,Member_real_info.member_id==Member.id,Member_pay_info.member_id==Member.id)
        render_data['real_name'] = query[0][1].real_name
        render_data['id_card'] = query[0][1].real_identid
        render_data['product_name'] = product_name
        render_data['time'] = datetime.strftime(datetime.now(),'%Y年%m月%d日')
    except:
        pass
    return render_template('html5/letter_of_authorization.html',render_data=render_data)


@app.route('/v1/html5/invate/<code>')
def invate(code):
    render_data = {'code': ''}
    member = Member.query.filter_by(invitation_code=code).first()
    if member:
        render_data['code'] = code
    return render_template('html5/yaoqing.html',render_data=render_data)


@app.route('/v1/html5/invate/ajax')
def invate_ajax():
    phone = request.args.get('phone')
    code = request.args.get('code')
    response_data = {}
    if phone:
        inm = Member.query.filter(Member.invitation_code == code).first()
        if not inm:
            response_data['code'] = u'10005'
            response_data['desc'] = u'邀请链接无效'
            return toolkit.response(response_data, 200, None, True)
        if phone == inm.phone:
            response_data['code'] = u'10002'
            response_data['desc'] = u'用户名已注册'
            return toolkit.response(response_data, 200, None, True)

        is_create, info = do_register(phone)
        if is_create:
            inr = Member_invite_info(inviter_id=inm.id, invited_id=info.id,inviter_time=datetime.now().date())
            info.is_activate = 0
            # 将被邀请人跟邀请人建立邀请关系
            db.session.merge(info)
            db.session.add(inr)
            db.session.commit()
            # 发送短信
            datas = [150]
            send_message(phone, datas, 41260)
            response_data['code'] = u'10000'
            response_data['desc'] = u'注册成功'
        else:
            response_data['code'] = u'10004'
            response_data['desc'] = info
    else:
        response_data['code'] = u'10001'
        response_data['desc'] = u'手机号不能为空'
    return toolkit.response(response_data, 200, None, True)


# 风险评估
@app.route('/v1/html5/risk_evaluation')
def risk_evaluation():
    phone = request.args.get('phone')
    score = request.args.get('score')
    response_data = {'phone': phone}
    if score and phone:
        response_data['score'] = score
        member = Member.query.filter_by(phone=phone).first()
        if member:
            if int(score) == 16:
                member.fxpinggu = '保守型'
            elif int(score) > 13:
                member.fxpinggu = '保守型'
            elif int(score) > 12:
                member.fxpinggu = '稳健型'
            elif int(score) > 10:
                member.fxpinggu = '稳健型'
            else:
                member.fxpinggu = '积极型'
        db.session.merge(member)
        db.session.commit()

        return toolkit.response(response_data, 200, None, True)
    return render_template('html5/fengkong.html', response_data=response_data)


# 安全保障
@app.route('/v1/html5/anquan')
def anquan():
    return render_template('html5/anquan.html')


#新手帮助
@app.route('/v1/html5/newhelp')
def newhelp():
    return render_template('html5/bangzhuzx.html')


# 38活动获奖名单
@app.route('/v1/html5/sanbahj')
def sanbahj():
    return render_template('html5/sanbahj.html')


#抢红包攻略
@app.route('/v1/html5/hongbaogl')
def hongbaogl():
    response_data = {}
    islogin = request.args.get('islogin')
    if islogin:
        response_data['islogin'] = islogin
    return render_template('html5/hongbaogl.html',response_data=response_data)


# 易保全地址
@app.route('/v1/html5/yibaoquan/<preservationId>',methods=['GET', 'POST'])
def yibaoquan(preservationId):
    response_data = {}
    ss = requests.session()
    url =  JAVA_BAOQUAN_URL + '/jeecg/tjtyyBorrowController.do?getContractFileViewUrl'
    r = ss.post(url,data={'preservationId':preservationId},verify=False)
    text = json.loads(r.content)
    response_data['preservation_url'] = text
    return toolkit.response(response_data, 200, None, True)


@app.route('/v1/html5/yibaoquan/banner',methods=['GET', 'POST'])
@check_activity(activity_name='大富翁活动')
def yibaoquan_banner():
    response_data = {}
    if g.isnotauth is not None:
        response_data['islogin'] = 0
    else:
        response_data['islogin'] = 1
    return render_template('html5/yibaoquan.html',response_data=response_data)


@app.route('/v1/html5/yhcunguan/banner',methods=['GET', 'POST'])
def yhcunguan_banner():
    response_data = {}
    return render_template('html5/yhcunguan.html',response_data=response_data)


@app.route('/v1/html5/investmentInfo/<product_id>/<num>',methods=['GET', 'POST'])
def investmentInfo(product_id,num):
    response_data = {'num':num}
    p = request.args.get('p')
    res_dadata = {}
    replace_id = str(product_id).replace('-', '')
    if str(num) == '3':
        try:
            query_file_top = db.session.query(Borrow_file, Borrow_attachment)
            query_file_list = query_file_top.filter(
                and_(Borrow_file.borrowId == str(replace_id), Borrow_attachment.id == Borrow_file.id)).all()

            jiekuan_array = []
            zhiya_array = []
            tongyi_array = []
            need_data = {}
            for i in query_file_list:
                res_data = {}
                res_data['path'] = JAVA_BAOQUAN_URL + '/' + i[1].realpath
                res_data['name'] = i[1].attachmenttitle
                if '借款合同' in  res_data['name']:
                    jiekuan_array.append(res_data)
                    jiekuan_array = htsort(jiekuan_array)
                if '质押' in res_data['name']:
                    zhiya_array.append(res_data)
                    zhiya_array = htsort(zhiya_array)
                if '同意' in  res_data['name']:
                    tongyi_array.append(res_data)
                    tongyi_array = htsort(tongyi_array)

            need_data['borrow'] = jiekuan_array
            need_data['zhiya'] = zhiya_array
            need_data['tongyi'] = tongyi_array
            res_dadata['code'] = u'10000'
            res_dadata['desc'] = u''
            res_dadata['content'] = need_data
        except Exception as e:
            res_dadata['code'] = u'10004'
            res_dadata['desc'] = u'数据库操作失败'
            res_dadata['content'] = []
        if p:
            return toolkit.response(res_dadata, 200, None, True)
        else:
            return render_template('product/borrow_demo.html', response_data=response_data)

    query_detail = db.session.query(Product_info, Borrower_info, Product_info.borrow_id)
    query_result = query_detail.filter(Product_info.id == replace_id,Borrower_info.id == Product_info.borrow_id).first()

    if product_id and query_result:
  
        response_data["product_type"] = query_result[0].product_type \
                                        if query_result[0].product_type != '房产抵押' else '抵押贷'
        response_data["rate"] = query_result[0].rate
        response_data["time_limit"] = query_result[0].time_limit
        response_data["total_mount"] = query_result[0].total_mount
        response_data["product_status"] = str(query_result[0].product_status)
        response_data["repay_type"] = query_result[0].repay_type
        response_data["product_detail"] = query_result[0].product_detail
        response_data["product_loan_use"] = query_result[0].loan_use
        response_data["product_borrower"] = query_result[1].borrower_name
        query_top = db.session.query(Invest_info, Member)
        query_bottom = query_top.filter(Invest_info.product_id == str(replace_id),
                                        Member.id == Invest_info.member_id).order_by(Invest_info.time.desc()).all()

        lists = []
        for i in query_bottom:
            lists.append((convertPhone(i[1].phone),i[0].money,i[0].time.strftime('%Y-%m-%d')))

        response_data["borrower_list"] = lists
        response_data['boluo_url'] = JAVA_BAOQUAN_IMAGES_URL

        # ------------------------合同相关图片---------------------------
        query_image_top = db.session.query(Product_image,Product_borrower_image)
        query_image_list = query_image_top.filter(or_(Product_image.borrow_id == str(replace_id),
                                                      Product_borrower_image.borrower_id == str(replace_id))).all()
        images = []
        for i in query_image_list:
            if i[0]:
                images.append(JAVA_BAOQUAN_IMAGES_URL + i[0].image)
            else:
                images.append(JAVA_BAOQUAN_IMAGES_URL + i[1].image_url)
        response_data['images'] = list(set(images))
    return render_template('html5/investmentInfo.html',response_data=response_data,convertPhone=convertPhone)


@app.route('/v1/html5/expose/info',methods=['GET', 'POST'])
def expose_info():
    return render_template('disclosure/expose.html')


@app.route('/v1/html5/expose/data/info',methods=['GET', 'POST'])
def expose_data_info():
    response_data = {}
    # 投资总金额
    invest_total = db.session.query(func.sum(Invest_info.money)) \
        .filter().scalar()
    ques = db.session.query(func.count(Member.id)).scalar()
    person_num = 120000 + ques  # 注册总人数
    # tzgques = db.session.query(Invest_info, Member_real_info.member_id, Member_real_info.real_identid).filter(and_(
    #     Invest_info.member_id == str(Member_real_info.member_id).replace("-", ""))).all()
    t_list_ss = []
    invest_array = []
    month_array = []
    for t in range(0, 151, 30):
        ttt = datetime.now() + timedelta(days=-t)
        percentage_ms = db.session.query(func.sum(Invest_info.money)) \
            .filter().scalar()
        percentage_ms += 1000000000
        t_list_ss.append((ttt.month, percentage_ms or 0))
        invest_array.append(str(round(float(percentage_ms or 0) / 100000000, 2)))
        month_array.append(str(ttt.month))


    pro_num = Product_info.query.filter_by(product_status='5').all()
    response_data['pro_num'] = len(pro_num) + 4300  # 菠萝理财搓成合同数
    response_data['invest_total'] = invest_total + 1000000000  # 投资总额
    response_data['invest_total_bill'] = (float(invest_total) + 1000000000.0) / 100000000.0
    response_data['person_num'] = person_num  # 人数
    response_data['invest_month'] = month_array[::-1]  # 投资月份
    response_data['invest_array'] = ','.join(invest_array[::-1])
    response_data['stroke_count_list'] = []  # 累计投资笔数占比
    response_data['time'] = datetime.strftime(datetime.now(), '%Y年%m月%d日')
    response_data['percentage'] = [('四川省', '9.6'), ('江苏省', '8.6'), ('山东省', '6.9'), ('河南省', '6.6'), ('广东省', '6.5')]

    # s = {'11':'北京市','12':'天津市','13':'河北省','14':'山西省','15':'内蒙古自治区','21':'辽宁省','22':'吉林省','23':'黑龙江省',
    #      '31':'上海市','32':'江苏省','33':'浙江省','34':'安徽省','35':'福建省','36':'江西省','37':'山东省','41':'河南省',\
    #      '42':'湖北省','44':'广东省','45':'广西壮族自治区','46':'海南省','50':'重庆市','51':'四川省','52':'贵州省','53':'云南省',
    #      '54': '西藏自治区', '61': '陕西省', '62': '甘肃省', '63': '青海省', '64': '宁夏回族自治区', '65': '新疆维吾尔自治区'}
    #
    # sfzdict = {}
    # for q in tzgques:
    #     sqri = str(q.real_identid[:2])
    #
    #     if s.has_key(sqri):
    #         if not sfzdict.has_key(s[sqri]):
    #             sfzdict[s[sqri]] = 0
    #         sfzdict[s[sqri]] += q[0].money
    # sfzlist = sfzdict.items()
    # sfzlist.sort(key=lambda x:x[1], reverse=True)
    # sfzlist = sfzlist[:5]
    #
    # percentage = [(k,round(v/invest_total,3)) for k,v in sfzlist]
    #
    # response_data['percentage'] = percentage
    return render_template('disclosure/expose-data.html', response_data=response_data)


@app.route('/v1/html5/expose/data/info/ajax',methods=['GET', 'POST'])
def expose_data_info_ajax():
    response_data = {}
    invest_list_top = db.session.query(Invest_info.time, Invest_info.money, Invest_info.hongbao)
    ybd = datetime.now() + timedelta(days=-103)
    invest_list = invest_list_top.filter(and_(Invest_info.time >= ybd)).all()
    invest_money_f01 = 0
    invest_money_f02 = 0
    invest_money_f03 = 0
    invest_money_f04 = 0
    for i in invest_list:
        if i.money + i.hongbao >= 0 and i.money + i.hongbao < 10000:
            invest_money_f01 += 1
        elif i.money + i.hongbao >= 10000 and i.money + i.hongbao < 30000:
            invest_money_f02 += 1
        elif i.money + i.hongbao >= 30000 and i.money + i.hongbao < 50000:
            invest_money_f03 += 1
        elif i.money + i.hongbao >= 50000 and i.money + i.hongbao < 100000:
            invest_money_f04 += 1

    stroke_count_list = [invest_money_f01, invest_money_f02, invest_money_f03, invest_money_f04]
    stroke_count_list_total = float(invest_money_f01 + invest_money_f02 + invest_money_f03 + invest_money_f04)
    stroke_count_list = [round(float(x) / stroke_count_list_total, 2) * 100 for x in stroke_count_list]
    response_data['stroke_count_list'] = stroke_count_list

    tttt = datetime.now() + timedelta(days=-83)
    real_info_tops = db.session.query(Member_real_info.real_identid)
    ages = real_info_tops.filter(Member_real_info.create_time > tttt).all()
    agearr = [0.0, 0.0, 0.0, 0.0]
    sexdic = {'man': 0, 'women': 0}
    for i in ages:
        idcard = i.real_identid
        if 1960 <= int(idcard[6:10]) < 1970:
            agearr[0] += 1.0
        elif 1970 <= int(idcard[6:10]) < 1980:
            agearr[1] += 1.0
        elif 1980 <= int(idcard[6:10]) < 1990:
            agearr[2] += 1.0
        elif 1990 <= int(idcard[6:10]) < 2000:
            agearr[3] += 1.0
        else:
            pass
        if int(idcard[-2]) % 2 == 1:
            sexdic['man'] += 1
        elif int(idcard[-2]) % 2 == 0:
            sexdic['women'] += 1
    total = sexdic['man'] + sexdic['women']

    agetotal = sum(agearr)
    agearr = [str(round(x / agetotal, 2) * 100) for x in agearr]

    sexdic['man'] = sexdic['man'] / total * 100
    sexdic['women'] = sexdic['women'] / total * 100
    response_data['ages'] = agearr  # 年龄比例
    response_data['sex'] = sexdic  # 性别比例
    return toolkit.response(response_data, 200, None, True)


@app.route('/v1/html5/expose/info/register_agreement',methods=['GET', 'POST'])
def register_agreement():
    return render_template('disclosure/xieyi.html')


@app.route('/v1/html5/expose/info/framework',methods=['GET', 'POST'])
def framework():
    return render_template('disclosure/jiagou.html')



@app.route('/v1/html5/expose/info/important_Things',methods=['GET', 'POST'])
def important_Things():
    return render_template('disclosure/zdshix.html')


@app.route('/v1/html5/ranking',methods=['GET', 'POST'])
def ranking():
    response_data = {}
    today = datetime.now()
    lastmonthformat = create_format(month_ago=1)
    print lastmonthformat

    array = creat_rank_list()[0]
    last_month_ncarray = creat_rank_list(month_ago= 1)[1]
    array_length = len(array[:10])
    num_array = map(str,range(1,array_length + 1))
    response_data['rank'] = zip(array[:10],num_array)
    month_dict = {'1':'一月','2':'二月','3':'三月','4':'四月','5':'五月','6':'六月','7':'七月','8':'八月','9':'九月','10':'十月','11':'十一月','12':'十二月'}
    response_data['month'] = month_dict[str(today.month)]


    if today.day == 1 and today.hour > 8:
        # 从上个月取排行是否有该字段
        send = Rank_list.query.filter_by(id='1dc5deb73a70463faf6e4032111982c4').first()
        value = Rank_list.query.filter_by(month=lastmonthformat).order_by(Rank_list.rank.asc()).all()
        if value:
            if send.is_send == 0:
                send_pinapple(value)
                send.is_send = 1
                db.session.merge(send)
                db.session.commit()
            else:
                # already send
                pass
        else:
            sort = 1
            for i in last_month_ncarray:
                new = Rank_list(phone=i[1], month=lastmonthformat, money=i[0], rank=sort)
                db.session.add(new)
                sort += 1
            send.is_send = 0
            db.session.merge(send)
            db.session.commit()
    return render_template('html5/monthly.html', response_data=response_data)


# 安全升级感恩回馈
@app.route('/v1/html5/4yue/gehk',methods=['GET', 'POST'])
def gehk():
    response_data = {}
    phone = request.args.get('phone')
    if phone:
        gehk_obj = Activity.query.filter_by(name='安全升级感恩回馈').first()
        if gehk_obj and gehk_obj.start_time < datetime.now() < gehk_obj.end_time and phone:
            member = Member.query.filter_by(phone=phone).first()
            if member:
                que_top = db.session.query(Member_red_pocket, Member_red_pocket_type.name)
                ll = ['安全升级回馈28元理财红包', '安全升级回馈158元理财红包', '安全升级回馈328元理财红包']
                ques = que_top.filter(and_(Member_red_pocket.sort_id==Member_red_pocket_type.id,
                                           Member_red_pocket.member_id==member.id))
                for l in ll:
                    q = ques.filter(Member_red_pocket_type.name==l).first()
                    if not q:
                        mrpt = Member_red_pocket_type.query.filter_by(name=l).first()
                        lc_red_pocket(member.id, mrpt.id)
                        lc_red_pocket(member.id, mrpt.id)
                response_data['login_in'] = 'true'
            else:
                response_data['login_in'] = 'false'
    return render_template('html5/gehk.html',response_data=response_data)


# h5未登录
@app.route('/v1/html5/login',methods=['GET', 'POST'])
def h5_login():
    return render_template('html5/dengl.html')


#跳转到维护界面
@app.route('/v1/html5/maintenance',methods=['GET','POST'])
def h5_maintenance():
    return render_template('html5/maintenance.html')


#获奖名单
@app.route('/v1/activity/mothersday/winner', methods=['GET', 'POST'])
def winner():
    return render_template('html5/may_award.html')


#合规
@app.route('/v1/html5/compliance', methods=['GET', 'POST'])
def compliance():
    return render_template('html5/compliance.html')


@app.route('/v1/html5/honor', methods=['GET', 'POST'])
def honor():
    return render_template('disclosure/honor.html')


@app.route('/v1/html5/dazhuanpan', methods=['GET', 'POST'])
def dazhuanpan():
    return render_template('html5/dazhuanpan.html')


# 借款相关合同
@app.route('/v1/html5/borrow_contract/<product_id>/<type_id>')
def borrow_contract_d(product_id, type_id):
    render_data = {}
    replace_id = str(product_id).replace('-', '')
    try:
        borrow = Product_info.query.filter_by(id=replace_id).first()
        if borrow:
            borrower_info = Borrower_info.query.filter_by(id=borrow.borrow_id).first()
            guarantor_info = Account_info.query.filter_by(id=borrow.guarantee_id).first()

            # 借款产品信息
            render_data['product_name'] = borrow.product_name  # 产品名称

            pattern = re.compile(r'[0-9]+')
            match = pattern.search(render_data['product_name'])
            if match:
                render_data['contract_no'] = match.group()  # 合同编号
            else:
                render_data['contract_no'] = render_data['product_name']

            render_data['rate'] = borrow.rate * 100  # 年化利率
            render_data['total_mount'] = borrow.total_mount  # 借款金额
            render_data['total_mount_chinese'] = cncurrency(render_data['total_mount'])  # 借款金额汉字大写
            render_data['loan_use'] = borrow.loan_use  # 借款用途
            render_data['time_limit'] = borrow.time_limit  # 借款期限
            render_data['time_limit_month'] = int(borrow.time_limit) / 30  # 借款期限月份显示
            render_data['car_message'] = borrow.car_message  # 质押财产车名
            if render_data['car_message'] is None:
                render_data['car_message'] = ''

            # 借款人信息
            if borrower_info:
                if borrow.product_type == '信贷宝':
                    render_data['borrower_name'] = hide_some_fields(borrower_info.borrower_name,
                                                                    type='both', before=2, back=4)  # 借款企业名称
                    render_data['borrower_id_card_type'] = '营业执照'
                else:
                    render_data['borrower_name'] = hide_some_fields(borrower_info.borrower_name,
                                                                             type='before', before=1)  # 借款人名称
                    render_data['borrower_id_card_type'] = '身份证'

                render_data['borrower_id_card'] = hide_some_fields(borrower_info.id_card,
                                                                                type='both', before=3, back=1)  # 借款人身份证号
                render_data['borrower_address'] = hide_some_fields(borrower_info.borrower_address,
                                                                                type='before', before=3)  # 借款人地址
                render_data['borrower_mobile'] = hide_some_fields(borrower_info.mobile,
                                                                               type='both', before=3, back=3)  # 借款人电话

            # 担保人信息
            if guarantor_info:
                render_data['guarantor_id_card'] = hide_some_fields(guarantor_info.id_card,
                                                                                 type='before', before=2)  # 担保人身份证号
    except:
        pass

    if type_id == '1':  # 借款合同
        return render_template('survey/borrow_demo.html', render_data=render_data)
    elif type_id == '2':  # 质押反担保合同
        return render_template('survey/pledge.html', render_data=render_data)
    elif type_id == '3':  # 同意担保函
        return render_template('survey/guarantee.html', render_data=render_data)
    else:
        return 'no result!'


# 项目详情
@app.route('/v1/html5/productInfo/<product_id>/<num>', methods=['GET', 'POST'])
def product_info(product_id, num):
    response_data = {'num': num}
    replace_id = str(product_id).replace('-', '')

    query_detail = db.session.query(Product_info, Borrower_info, Product_info.borrow_id)
    query_result = query_detail.filter(Product_info.id == replace_id,
                                       Borrower_info.id == Product_info.borrow_id).first()

    if product_id and query_result:
        # 项目概况
        response_data["product_id"] = product_id
        response_data["product_type"] = query_result[0].product_type \
            if query_result[0].product_type != '房产抵押' else '抵押贷'
        response_data["rate"] = query_result[0].rate
        response_data["time_limit"] = query_result[0].time_limit
        response_data["total_mount"] = query_result[0].total_mount
        response_data["limit_mount"] = query_result[0].limit_mount
        response_data["product_status"] = str(query_result[0].product_status)
        response_data["repay_type"] = query_result[0].repay_type
        response_data["product_detail"] = query_result[0].product_detail
        response_data["product_loan_use"] = query_result[0].loan_use
        response_data["product_borrower"] = query_result[1].borrower_name
        response_data['product_type'] = query_result[0].product_type

        # 投资人信息
        query_top = db.session.query(Invest_info, Member)
        query_bottom = query_top.filter(Invest_info.product_id == str(replace_id),
                                        Member.id == Invest_info.member_id, Invest_info.is_effect==1).order_by(Invest_info.time.desc()).all()
        lists = []
        for i in query_bottom:
            lists.append((convertPhone(i[1].phone), i[0].money, i[0].time.strftime('%Y-%m-%d')))
        response_data["borrower_list"] = lists

        # 借款相关合同
        response_data['borrow_demo'] = "%s/v1/html5/borrow_contract/%s/1" % (BOLUO_URL, product_id)
        response_data['guarantee'] = "%s/v1/html5/borrow_contract/%s/3" % (BOLUO_URL, product_id)
        response_data['pledge'] = "%s/v1/html5/borrow_contract/%s/2" % (BOLUO_URL, product_id)

        # 相关图片
        query_image_top = db.session.query(Product_image, Product_borrower_image)
        query_image_list = query_image_top.filter(or_(Product_image.borrow_id == str(replace_id),
                                                      Product_borrower_image.borrower_id == str(replace_id))).all()
        images = []
        for i in query_image_list:
            if i[0]:
                images.append(JAVA_BAOQUAN_IMAGES_URL + i[0].image)
            else:
                images.append(JAVA_BAOQUAN_IMAGES_URL + i[1].image_url)
        response_data['images'] = list(set(images))

    if num == '0':
        return render_template('survey/project.html', response_data=response_data, convertPhone=convertPhone)
    elif num == '1':
        return render_template('survey/purchase.html', response_data=response_data, convertPhone=convertPhone)
    elif num == '2':
        return render_template('survey/project_tab.html', response_data=response_data, convertPhone=convertPhone)
