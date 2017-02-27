# -*- coding: utf-8 -*-
import time
import string
import random
import hashlib
import urllib2
import requests

try:
    from flask import request
except ImportError:
    request = None

try:
    from xml.etree import cElementTree as ETree
except ImportError:
    from xml.etree import ElementTree as ETree


class WxPayError(Exception):
    def __init__(self, msg):
        super(WxPayError, self).__init__(msg)


class WxPay(object):
    def __init__(self, wx_app_id, wx_mch_id, wx_mch_key, wx_notify_url):
        self.opener = urllib2.build_opener(urllib2.HTTPSHandler())
        self.WX_APP_ID = wx_app_id
        self.WX_MCH_ID = wx_mch_id
        self.WX_MCH_KEY = wx_mch_key
        self.WX_NOTIFY_URL = wx_notify_url

    @staticmethod
    def user_ip_address():
        return request.remote_addr if request else None

    @staticmethod
    def nonce_str(length=32):
        char = string.ascii_letters + string.digits
        return "".join(random.choice(char) for _ in range(length))

    @staticmethod
    def to_utf8(raw):
        return raw.encode("utf-8") if isinstance(raw, unicode) else raw

    @staticmethod
    def to_dict(content):
        raw = {}
        root = ETree.fromstring(content)
        for child in root:
            raw[child.tag] = child.text
        return raw

    @staticmethod
    def random_num(length):
        digit_list = list(string.digits)
        random.shuffle(digit_list)
        return ''.join(digit_list[:length])

    def sign(self, raw):
        """
        生成签名
        参考微信签名生成算法
        https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=4_3
        """
        raw = [(k, str(raw[k]) if isinstance(raw[k], (int, float)) else raw[k]) for k in sorted(raw.keys())]
        s = "&".join("=".join(kv) for kv in raw if kv[1])
        s += "&key={0}".format(self.WX_MCH_KEY)
        return hashlib.md5(self.to_utf8(s)).hexdigest().upper()

    def check(self, raw):
        """
        验证签名是否正确
        """
        sign = raw.pop("sign")
        return sign == self.sign(raw)

    def to_xml(self, raw):
        s = ""
        for k, v in raw.iteritems():
            s += "<{0}>{1}</{0}>".format(k, self.to_utf8(v), k)
        return "<xml>{0}</xml>".format(s)

    def fetch(self, url, data):
        req = urllib2.Request(url, data=self.to_xml(data))
        try:
            resp = self.opener.open(req, timeout=20)
        except urllib2.HTTPError, e:
            resp = e
        re_info = resp.read()
        try:
            return self.to_dict(re_info)
        except ETree.ParseError:
            return re_info

    def fetch_with_ssl(self, url, data, api_client_cert_path, api_client_key_path):
        req = requests.post(url, data=self.to_xml(data),
                            cert=(api_client_cert_path, api_client_key_path))
        return self.to_dict(req.content)

    def reply(self, msg, ok=True):
        code = "SUCCESS" if ok else "FAIL"
        return self.to_xml(dict(return_code=code, return_msg=msg))

    def unified_order(self, **data):
        """
        统一下单
        详细规则参考 https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=9_1

        :param data: out_trade_no, body, total_fee, trade_type
            out_trade_no: 商户订单号
            body: 商品描述
            total_fee: 标价金额, 整数, 单位 分
            trade_type: 交易类型
            user_ip 在flask框架下可以自动填写, 非flask框架需传入spbill_create_ip
        :return: 统一下单生成结果
        """
        url = "https://api.mch.weixin.qq.com/pay/unifiedorder"

        # 必填参数
        if "out_trade_no" not in data:
            raise WxPayError(u"缺少统一支付接口必填参数out_trade_no")
        if "body" not in data:
            raise WxPayError(u"缺少统一支付接口必填参数body")
        if "total_fee" not in data:
            raise WxPayError(u"缺少统一支付接口必填参数total_fee")
        if "trade_type" not in data:
            raise WxPayError(u"缺少统一支付接口必填参数trade_type")

        # 关联参数
        if data["trade_type"] == "JSAPI" and "openid" not in data:
            raise WxPayError(u"trade_type为JSAPI时，openid为必填参数")
        if data["trade_type"] == "NATIVE" and "product_id" not in data:
            raise WxPayError(u"trade_type为NATIVE时，product_id为必填参数")
        user_ip = self.user_ip_address()
        if not user_ip and "spbill_create_ip" not in data:
            raise WxPayError(u"当前未使用flask框架，缺少统一支付接口必填参数spbill_create_ip")

        data.setdefault("appid", self.WX_APP_ID)
        data.setdefault("mch_id", self.WX_MCH_ID)
        data.setdefault("notify_url", self.WX_NOTIFY_URL)
        data.setdefault("nonce_str", self.nonce_str())
        data.setdefault("spbill_create_ip", user_ip)
        data.setdefault("sign", self.sign(data))

        raw = self.fetch(url, data)
        if raw["return_code"] == "FAIL":
            raise WxPayError(raw["return_msg"])
        err_msg = raw.get("err_code_des")
        if err_msg:
            raise WxPayError(err_msg)
        return raw

    def js_pay_api(self, **kwargs):
        """
        生成给JavaScript调用的数据
        详细规则参考 https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=7_7&index=6

        :param kwargs: openid, body, total_fee
            openid: 用户openid
            body: 商品名称
            total_fee: 标价金额, 整数, 单位 分
            out_trade_no: 商户订单号, 若未传入则自动生成
        :return: 生成微信JS接口支付所需的信息
        """
        kwargs.setdefault("trade_type", "JSAPI")
        if "out_trade_no" not in kwargs:
            kwargs.setdefault("out_trade_no", self.nonce_str())
        raw = self.unified_order(**kwargs)
        package = "prepay_id={0}".format(raw["prepay_id"])
        timestamp = int(time.time())
        nonce_str = self.nonce_str()
        raw = dict(appId=self.WX_APP_ID, timeStamp=timestamp,
                   nonceStr=nonce_str, package=package, signType="MD5")
        sign = self.sign(raw)
        return dict(package=package, appId=self.WX_APP_ID,
                    timeStamp=timestamp, nonceStr=nonce_str, sign=sign)

    def order_query(self, **data):
        """
        订单查询
        详细规则参考 https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=9_2

        :param data: out_trade_no, transaction_id至少填一个
            out_trade_no: 商户订单号
            transaction_id: 微信订单号
        :return: 订单查询结果
        """
        url = "https://api.mch.weixin.qq.com/pay/orderquery"

        if "out_trade_no" not in data and "transaction_id" not in data:
            raise WxPayError(u"订单查询接口中，out_trade_no、transaction_id至少填一个")
        data.setdefault("appid", self.WX_APP_ID)
        data.setdefault("mch_id", self.WX_MCH_ID)
        data.setdefault("nonce_str", self.nonce_str())
        data.setdefault("sign", self.sign(data))

        raw = self.fetch(url, data)
        if raw["return_code"] == "FAIL":
            raise WxPayError(raw["return_msg"])
        return raw

    def close_order(self, out_trade_no):
        """
        关闭订单
        详细规则参考 https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=9_3

        :param out_trade_no: 商户订单号
        :return: 申请关闭订单结果
        """
        url = "https://api.mch.weixin.qq.com/pay/closeorder"
        data = {
            'out_trade_no': out_trade_no,
            'appid': self.WX_APP_ID,
            'mch_id': self.WX_MCH_ID,
            'nonce_str': self.nonce_str(),
        }
        data["sign"] = self.sign(data)
        raw = self.fetch(url, data)
        if raw["return_code"] == "FAIL":
            raise WxPayError(raw["return_msg"])
        return raw

    def refund(self, api_cert_path, api_key_path, **data):
        """
        申请退款
        详细规则参考 https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=9_4

        :param api_cert_path: 微信支付商户证书路径，此证书(apiclient_cert.pem)需要先到微信支付商户平台获取，下载后保存至服务器
        :param api_key_path: 微信支付商户证书路径，此证书(apiclient_key.pem)需要先到微信支付商户平台获取，下载后保存至服务器
        :param data: out_trade_no、transaction_id至少填一个, out_refund_no, total_fee, refund_fee
            out_trade_no: 商户订单号
            transaction_id: 微信订单号
            out_refund_no: 商户退款单号（若未传入则自动生成）
            total_fee: 订单金额
            refund_fee: 退款金额
        :return: 退款申请返回结果
        """
        url = "https://api.mch.weixin.qq.com/secapi/pay/refund"
        if "out_trade_no" not in data and "transaction_id" not in data:
            raise WxPayError(u"订单查询接口中，out_trade_no、transaction_id至少填一个")
        if "total_fee" not in data:
            raise WxPayError(u"退款申请接口中，缺少必填参数total_fee")
        if "refund_fee" not in data:
            raise WxPayError(u"退款申请接口中，缺少必填参数refund_fee")
        if "out_refund_no" not in data:
            data.setdefault("out_refund_no", self.nonce_str())

        data.setdefault("appid", self.WX_APP_ID)
        data.setdefault("mch_id", self.WX_MCH_ID)
        data.setdefault("op_user_id", self.WX_MCH_ID)
        data.setdefault("nonce_str", self.nonce_str())
        data.setdefault("sign", self.sign(data))

        raw = self.fetch_with_ssl(url, data, api_cert_path, api_key_path)
        if raw["return_code"] == "FAIL":
            raise WxPayError(raw["return_msg"])
        return raw

    def refund_query(self, **data):
        """
        查询退款
        提交退款申请后，通过调用该接口查询退款状态。退款有一定延时，
        用零钱支付的退款20分钟内到账，银行卡支付的退款3个工作日后重新查询退款状态。
        详细规则参考 https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=9_5

        :param data: out_refund_no、out_trade_no、transaction_id、refund_id四个参数必填一个
            out_refund_no: 商户退款单号
            out_trade_no: 商户订单号
            transaction_id: 微信订单号
            refund_id: 微信退款单号

        :return: 退款查询结果
        """
        url = "https://api.mch.weixin.qq.com/pay/refundquery"
        if "out_refund_no" not in data and "out_trade_no" not in data \
                and "transaction_id" not in data and "refund_id" not in data:
            raise WxPayError(u"退款查询接口中，out_refund_no、out_trade_no、transaction_id、refund_id四个参数必填一个")

        data.setdefault("appid", self.WX_APP_ID)
        data.setdefault("mch_id", self.WX_MCH_ID)
        data.setdefault("nonce_str", self.nonce_str())
        data.setdefault("sign", self.sign(data))

        raw = self.fetch(url, data)
        if raw["return_code"] == "FAIL":
            raise WxPayError(raw["return_msg"])
        return raw

    def download_bill(self, bill_date, bill_type=None):
        """
        下载对账单
        详细规则参考 https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=9_6

        :param bill_date: 对账单日期
        :param bill_type: 账单类型(ALL-当日所有订单信息，[默认]SUCCESS-当日成功支付的订单, REFUND-当日退款订单)

        :return: 数据流形式账单
        """
        url = "https://api.mch.weixin.qq.com/pay/downloadbill"
        data = {
            'bill_date': bill_date,
            'bill_type': bill_type if bill_type else 'SUCCESS',
            'appid': self.WX_APP_ID,
            'mch_id': self.WX_MCH_ID,
            'nonce_str': self.nonce_str()
        }
        data['sign'] = self.sign(data)
        raw = self.fetch(url, data)
        return raw

    def send_red_pack(self, api_cert_path, api_key_path, **data):
        """
        发给用户微信红包
        详细规则参考 https://pay.weixin.qq.com/wiki/doc/api/tools/cash_coupon.php?chapter=13_4&index=3

        :param api_cert_path: 微信支付商户证书路径，此证书(apiclient_cert.pem)需要先到微信支付商户平台获取，下载后保存至服务器
        :param api_key_path: 微信支付商户证书路径，此证书(apiclient_key.pem)需要先到微信支付商户平台获取，下载后保存至服务器
        :param data: send_name, re_openid, total_amount, wishing, client_ip, act_name, remark
            send_name: 商户名称 例如: 天虹百货
            re_openid: 用户openid
            total_amount: 付款金额
            wishing: 红包祝福语 例如: 感谢您参加猜灯谜活动，祝您元宵节快乐！
            client_ip: 调用接口的机器Ip地址, 注：此地址为服务器地址
            act_name: 活动名称 例如: 猜灯谜抢红包活动
            remark: 备注 例如: 猜越多得越多，快来抢！
        :return: 红包发放结果
        """
        url = "https://api.mch.weixin.qq.com/mmpaymkttransfers/sendredpack"
        if "send_name" not in data:
            raise WxPayError(u"向用户发送红包接口中，缺少必填参数send_name")
        if "re_openid" not in data:
            raise WxPayError(u"向用户发送红包接口中，缺少必填参数re_openid")
        if "total_amount" not in data:
            raise WxPayError(u"向用户发送红包接口中，缺少必填参数total_amount")
        if "wishing" not in data:
            raise WxPayError(u"向用户发送红包接口中，缺少必填参数wishing")
        if "client_ip" not in data:
            raise WxPayError(u"向用户发送红包接口中，缺少必填参数client_ip")
        if "act_name" not in data:
            raise WxPayError(u"向用户发送红包接口中，缺少必填参数act_name")
        if "remark" not in data:
            raise WxPayError(u"向用户发送红包接口中，缺少必填参数remark")

        data.setdefault("wxappid", self.WX_APP_ID)
        data.setdefault("mch_id", self.WX_MCH_ID)
        data.setdefault("nonce_str", self.nonce_str())
        data.setdefault("mch_billno", u'{0}{1}{2}'.format(
            self.WX_MCH_ID, time.strftime('%Y%m%d', time.localtime(time.time())), self.random_num(10)
        ))
        data.setdefault("total_num", 1)
        data.setdefault("scene_id", 'PRODUCT_4')
        data.setdefault("sign", self.sign(data))

        raw = self.fetch_with_ssl(url, data, api_cert_path, api_key_path)
        if raw["return_code"] == "FAIL":
            raise WxPayError(raw["return_msg"])
        return raw

    def enterprise_payment(self, api_cert_path, api_key_path, **data):
        """
        使用企业对个人付款功能
        详细规则参考 https://pay.weixin.qq.com/wiki/doc/api/tools/mch_pay.php?chapter=14_2

        :param api_cert_path: 微信支付商户证书路径，此证书(apiclient_cert.pem)需要先到微信支付商户平台获取，下载后保存至服务器
        :param api_key_path: 微信支付商户证书路径，此证书(apiclient_key.pem)需要先到微信支付商户平台获取，下载后保存至服务器
        :param data: openid, check_name, re_user_name, amount, desc, spbill_create_ip
            openid: 用户openid
            check_name: 是否校验用户姓名
            re_user_name: 如果 check_name 为True，则填写，否则不带此参数
            amount: 金额: 企业付款金额，单位为分
            desc: 企业付款描述信息
            spbill_create_ip: 调用接口的机器Ip地址, 注：此地址为服务器地址
        :return: 企业转账结果
        """
        url = "https://api.mch.weixin.qq.com/mmpaymkttransfers/promotion/transfers"
        if "openid" not in data:
            raise WxPayError(u"企业付款申请接口中，缺少必填参数openid")
        if "check_name" not in data:
            raise WxPayError(u"企业付款申请接口中，缺少必填参数check_name")
        if data['check_name'] and "re_user_name" not in data:
            raise WxPayError(u"企业付款申请接口中，缺少必填参数re_user_name")
        if "amount" not in data:
            raise WxPayError(u"企业付款申请接口中，缺少必填参数amount")
        if "desc" not in data:
            raise WxPayError(u"企业付款申请接口中，缺少必填参数desc")
        if "spbill_create_ip" not in data:
            raise WxPayError(u"企业付款申请接口中，缺少必填参数spbill_create_ip")

        data.setdefault("mch_appid", self.WX_APP_ID)
        data.setdefault("mchid", self.WX_MCH_ID)
        data.setdefault("nonce_str", self.nonce_str())
        data.setdefault("partner_trade_no", u'{0}{1}{2}'.format(
            self.WX_MCH_ID, time.strftime('%Y%m%d', time.localtime(time.time())), self.random_num(10)
        ))
        data['check_name'] = 'FORCE_CHECK' if data['check_name'] else 'NO_CHECK'
        data.setdefault("sign", self.sign(data))

        raw = self.fetch_with_ssl(url, data, api_cert_path, api_key_path)
        if raw["return_code"] == "FAIL":
            raise WxPayError(raw["return_msg"])
        return raw
