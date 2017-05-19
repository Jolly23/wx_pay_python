# 微信支付

参考文档 [https://pay.weixin.qq.com/wiki/doc/api/jsapi.php](https://pay.weixin.qq.com/wiki/doc/api/jsapi.php)

## 使用

首先引入包
```python
    from wx_pay import WxPay, WxPayError
```

构造微信支付类，传入配置微信支付参数
```python
    wx_pay = WxPay(
        wx_app_id='WX_APP_ID',  # 微信平台appid
        wx_mch_id='WX_MCH_ID',  # 微信支付商户号
        wx_mch_key='WX_MCH_KEY',
        # wx_mch_key 微信支付重要密钥，请登录微信支付商户平台，在 账户中心-API安全-设置API密钥设置
        wx_notify_url='http://www.example.com/pay/weixin/notify'
        # wx_notify_url 接受微信付款消息通知地址（通常比自己把支付成功信号写在js里要安全得多，推荐使用这个来接收微信支付成功通知）
        # wx_notify_url 开发详见https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=9_7
    )
```

创建订单
```python
    data = wx_pay.js_pay_api(
            openid=u'***user_openid***',  # 付款用户openid
            body=u'***商品名称/付款显示名称***',  # 例如：饭卡充值100元
            total_fee=100  # total_fee 单位是 分， 100 = 1元
        )
```

查询订单
```python
    data = wx_pay.order_query(
        # 下面两个参数二选一
        out_trade_no=u'***商户订单号***',
        # transaction_id=u'***微信订单号***'
    )
```

关闭订单
```python
    data = wx_pay.close_order(
        out_trade_no=u'***商户订单号***'
    )
```

申请退款
```python
    data = wx_pay.refund(
        # 证书获取方法请阅读：https://pay.weixin.qq.com/wiki/doc/api/tools/cash_coupon.php?chapter=4_3
        # api_cert_path: 微信支付商户证书（apiclient_cert.pem）的本地保存路径
        api_cert_path='/home/xxx/SERVER/ext_file/apiclient_cert.pem',
        # api_cert_path: 微信支付商户证书（apiclient_key.pem）的本地保存路径
        api_key_path='/home/xxx/SERVER/ext_file/apiclient_key.pem',
        out_trade_no=u'***商户订单号***',
        # out_refund_no=u'***商户退款单号***',   商户退款单号可自动生成，按需使用
        total_fee=500,  # 支付时下单总金额 单位分
        refund_fee=500,  # 要退款的金额 单位分
    )
```

退款查询
```python
    data = wx_pay.refund_query(
        # 以下传入参数四选一即可
        out_refund_no=u'***商户退款单号***',
        # out_trade_no=u'***商户订单号***',
        # transaction_id=u'***微信订单号***',
        # refund_id=u'***微信退款单号***',
    )
```

下载对账单
```python
    print wx_pay.download_bill(
        # 对账单日期
        bill_date='20161228',  
        # 账单类型(ALL-当日所有订单信息，[默认]SUCCESS-当日成功支付的订单, REFUND-当日退款订单)
        bill_type='ALL'  
    )
```
        
给用户发红包（使用前需要到微信支付产品中心开通此功能）
```python
    wx_pay.send_red_pack(
        # 证书获取方法请阅读：https://pay.weixin.qq.com/wiki/doc/api/tools/cash_coupon.php?chapter=4_3
        # api_cert_path: 微信支付商户证书（apiclient_cert.pem）的本地保存路径
        api_cert_path='/home/xxx/SERVER/ext_file/apiclient_cert.pem',
        # api_cert_path: 微信支付商户证书（apiclient_key.pem）的本地保存路径
        api_key_path='/home/xxx/SERVER/ext_file/apiclient_key.pem',
        send_name=u'***公众号发送红包测试***',  # 红包名称
        re_openid=u'***to_user_openid***',  # 要接收红包的用户openid
        total_amount=100,  # total_fee 单位是 分， 100 = 1元, 最大499元
        wishing=u'***感谢参与测试***',  # 祝福语
        client_ip=u'222.222.222.222',  # 调用微信发红包接口服务器公网IP地址
        act_name=u'***微信支付测试系统***',  # 活动名称
        remark=u'***感谢参与***'  # 备注
    )
```

用企业付款功能给用户转账（使用前需要到微信支付产品中心开通此功能）
```python
    wx_pay.enterprise_payment(
        # 证书获取方法请阅读：https://pay.weixin.qq.com/wiki/doc/api/tools/cash_coupon.php?chapter=4_3
        # api_cert_path: 微信支付商户证书（apiclient_cert.pem）的本地保存路径
        api_cert_path='/home/xxx/SERVER/ext_file/apiclient_cert.pem',
        # api_cert_path: 微信支付商户证书（apiclient_key.pem）的本地保存路径
        api_key_path='/home/xxx/SERVER/ext_file/apiclient_key.pem',
        openid=u'***to_user_openid***',  # 要接收转账的用户openid
        check_name=True,    # 是否强制校验收款用户姓名
        # 如果check_name为True，下面re_user_name必须传入
        # 如果check_name为False，请删除下一行参数re_user_name
        re_user_name=u'***客户的真实姓名***',  # 校验不成功付款会是失败
        amount=100,  # amount 单位是 分， 100 = 1元, 单用户 单笔上限／当日上限：2W／2W
        desc=u'充值失败退款', # 付款原因
        spbill_create_ip='222.222.222.222',  # 调用微信企业付款接口服务器公网IP地址
    )
```

提交刷卡支付请求（通过微信钱包付款码的方式付款）
商户需可通过 设备扫码 等方式获取到客户付款码，向微信提交支付请求
```python
    wx_pay.swiping_card_payment(
        body=u'***商品名称/付款显示名称***',  # 例如：综合超市
        total_fee=100,  # total_fee 单位是 分， 100 = 1元, 单用户 单笔上限／当日上限：2W／2W
        auth_code='131336161431593669', # 扫码支付授权码，设备读取用户微信中的条码或者二维码信息（注：用户刷卡条形码规则：18位纯数字，以10、11、12、13、14、15开头）
        spbill_create_ip='222.222.222.222',  # 调用微信企业付款接口服务器公网IP地址
    )
```

## 工具函数

签名
```python
    wx_pay.sign(dict(openid="xxxxxxxxxxxxxxxxxx", total_fee=100))
```

32位随机字符串
```python
    wx_pay.nonce_str()
```

验证签名
```python
    wx_pay.check(dict(openid="xxxxxxxxxxxxxxxxxx", total_fee=100, sign="signsignsignsign"))
```

生成微信前端JS配置参数
```text
    详见example.py的wx_js_config方法, 用来生成前端使用微信js的必要参数
```

## License
The MIT License(http://opensource.org/licenses/MIT)

请自由地享受和参与开源

## 贡献

如果你有好的意见或建议，欢迎给我们提issue或pull request，为提升Python调用微信支付体验贡献力量