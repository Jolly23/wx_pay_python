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
        wx_app_id='WX_APP_ID', 
        wx_mch_id='WX_MCH_ID', 
        wx_mch_key='WX_MCH_KEY',
        wx_notify_url='http://www.example.com/pay/weixin/notify'
    )
```

创建订单
```python
    pay_data = wx_pay.js_api(
            openid=u'***user_openid***',  # 付款用户openid
            body=u'***商品名称/付款显示名称***',  # 例如：饭卡充值100元
            total_fee=100  # total_fee 单位是 分， 100 = 1元
        )
```
        
给用户发红包
```python
    wx_pay.send_red_pack(
        api_client_cert_path='/home/xxx/SERVER/ext_file/wx_2_pay_cert.pem',
        api_client_key_path='/home/xxx/SERVER/ext_file/wx_2_pay_key.pem',
        send_name=u'公众号发送红包测试',  # 红包名称
        re_openid=u'***to_user_openid***',  # 要接收红包的用户openid
        total_amount=100,  # total_fee 单位是 分， 100 = 1元, 最大499元
        wishing=u'感谢参与测试',  # 祝福语
        client_ip=u'222.222.222.222',  # 调用微信发红包接口服务器公网IP地址
        act_name=u'微信支付测试系统',  # 活动名称
        remark=u'感谢参与'  # 备注
    )
```

查询订单
```python
    raw = wx_pay.close_order(out_trade_no)
```

关闭订单
```python
    raw = wx_pay.order_query(out_trade_no=out_trade_no)
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
```python
    详见example.py的wx_js_config方法，用来生成前端使用微信js的必要参数
```