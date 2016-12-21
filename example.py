#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import jsonify
from time import time
from hashlib import sha1

from wx_pay import WxPay, WxPayError


def wx_js_config():
    # 生成前端 调用微信js的配置参数
    config_args = {
        'noncestr': WxPay.nonce_str(),
        'jsapi_ticket': 'xxxxxx',
        # jsapi_ticket 一个类似ACCESS_TOKEN的参数，
        # 详见 https://mp.weixin.qq.com/wiki?action=doc&id=mp1421141115&t=0.6103989146089088#jssdkshiyongbuzhou
        'timestamp': int(time()),
        'url': 'http://www.example.com/pay/goods=3'     # 使用js_api的网页网址
    }
    raw = [(k, str(config_args[k]) if isinstance(config_args[k], (int, float)) else config_args[k])
           for k in sorted(config_args.keys())]
    s = "&".join("=".join(kv) for kv in raw if kv[1])
    return {
        'signature': sha1(s).hexdigest(),
        'timestamp': config_args['timestamp'],
        'nonce_str': config_args['noncestr']
    }


def create_pay_example():
    # 普通下单example
    wx_pay = WxPay(
        wx_app_id='WX_APP_ID',  # 微信平台appid
        wx_mch_id='WX_MCH_ID',  # 微信支付商户号
        wx_mch_key='WX_MCH_KEY',
        # wx_mch_key 微信支付重要密钥，请登录微信支付商户平台，在 账户中心-API安全-设置API密钥设置
        wx_notify_url='http://www.example.com/pay/weixin/notify'
        # wx_notify_url 接受微信付款消息通知地址（通常比自己把支付成功信号写在js里要安全得多，推荐使用这个来接收微信支付成功通知）
        # wx_notify_url 开发详见https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=9_7
    )
    try:
        pay_data = wx_pay.js_api(
            openid=u'***user_openid***',  # 付款用户openid
            body=u'***商品名称/付款显示名称***',  # 例如：饭卡充值100元
            total_fee=100  # total_fee 单位是 分， 100 = 1元
        )
        print pay_data
        # 订单生成后将请将返回的json数据 传入前端页面微信支付js的参数部分
        return jsonify(pay_data)
    except WxPayError, e:
        return e.message, 400


def send_red_pack_to_user_example():
    # 向个人用户发红包example
    wx_pay = WxPay(
        wx_app_id='WX_APP_ID',
        wx_mch_id='WX_MCH_ID',
        wx_mch_key='WX_MCH_KEY',
        wx_notify_url='WX_NOTIFY_URL'
    )
    wx_pay.send_red_pack(
        # 证书获取方法请阅读：https://pay.weixin.qq.com/wiki/doc/api/tools/cash_coupon.php?chapter=4_3
        # api_client_cert_path: 微信支付商户证书（apiclient_cert.pem）的本地保存路径
        api_client_cert_path='/home/xxx/SERVER/ext_file/wx_2_pay_cert.pem',
        # api_client_cert_path: 微信支付商户证书（apiclient_key.pem）的本地保存路径
        api_client_key_path='/home/xxx/SERVER/ext_file/wx_2_pay_key.pem',
        send_name=u'微信支付测试',  # 红包名称
        re_openid=u'***to_user_openid***',  # 要接收红包的用户openid
        total_amount=100,  # total_fee 单位是 分， 100 = 1元, 最大499元
        wishing=u'感谢参与测试',  # 祝福语
        client_ip=u'222.222.222.222',  # 调用微信发红包接口服务器公网IP地址
        act_name=u'微信支付测试系统',  # 活动名称
        remark=u'感谢参与'  # 备注
    )


if __name__ == "__main__":
    pass
