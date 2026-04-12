# 神经突触 App 版

这是独立的 `uni-app` App 工程，目录可直接用 HBuilderX 打开。

## 当前状态

- 已完成与小程序同一套审美风格的 App 版主界面
- 已落地用户侧核心链路：浏览、收藏、购物车、下单、支付页、订单、聊天、认证、发布
- 支持 `mock` 演示模式与 `HTTP API` 实际后端模式切换
- 支付层已预留 `uni.requestPayment` 调用桥

## 目录说明

- `common/service.js`：App 侧统一服务层
- `common/payment.js`：App 支付桥接
- `common/env.js`：切换演示模式 / 真实后端模式
- `pages/`：App 页面
- `components/BottomTabBar.vue`：底部导航栏

## 打开方式

1. 打开 HBuilderX
2. 选择“导入项目”
3. 选择当前 `app` 目录
4. 运行到 Android App 基座或打包自定义基座

## 真实接入前要改的地方

1. 把 `common/env.js` 里的 `useMock` 改为 `false`
2. 把 `apiBaseUrl` 改为你自己的 HTTPS API 地址
3. 把支付返回参数接到 `common/payment.js`
4. 用真实用户体系替换演示态的本地缓存数据
