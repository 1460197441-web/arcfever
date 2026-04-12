# 神经突触 Subagent 分工表与执行顺序

## 1. 总控规则

### 1.1 当前项目范围

当前仓库不是单一小程序，而是 3 条链路并存：

- 微信小程序前端：`/pages/*`、`/custom-tab-bar/*`、`/utils/*`
- 微信云开发后端：`/cloudfunctions/gateway/*`、`/cloudfunctions/bootstrap/*`
- App 端 `uni-app` 工程：`/app/*`

当前真实云数据库已存在这些核心集合：

- `users`
- `schools`
- `instruments`
- `agreements`
- `certifications`
- `categories`
- `favorites`
- `cart_items`
- `orders`
- `chats`
- `chat_messages`
- `ratings`
- `reports`
- `disputes`
- `posts`
- `projects`
- `ai_tasks`

### 1.2 总控 Agent 职责

总控由主代理承担，不大面积直接写业务功能，主要负责：

- 维护需求清单、优先级、阻塞项
- 统一数据模型、状态机、API 契约
- 约束各子代理只在自己的交付物范围内行动
- 把多个子代理的结果合并成一条可运行链路
- 做最终验收、自检、打包和风险清单

### 1.3 统一约束

所有子代理必须遵守：

- 先输出设计结论，再写代码
- 不得擅自改动跨域 API 契约
- 所有状态变化必须可追踪
- 所有页面必须考虑 `loading / empty / error`
- 所有交易行为必须考虑角色权限、幂等、异常回滚
- 代码提交前必须附带测试点和风险点

## 2. 逻辑工位与实际代理映射

当前会话里可用的实际执行单元有限，所以采用“8 个逻辑工位 + 1 个总控”的编排方式，再映射到现有代理。

### 2.1 逻辑工位

1. 产品需求工位
2. UI/交互工位
3. 小程序前端工位
4. App 前端工位
5. 后端领域工位
6. 库存与规则工位
7. 支付与通知工位
8. 测试与运维工位
9. 总控工位

### 2.2 映射到当前代理

- 总控工位：主代理
- 产品需求工位：主代理 + `Erdos`
- UI/交互工位：`Halley`
- 小程序前端工位：主代理
- App 前端工位：`Halley`
- 后端领域工位：`Aquinas`
- 库存与规则工位：`Erdos`
- 支付与通知工位：`Aquinas`
- 测试与运维工位：主代理

说明：

- `Erdos` 更适合承接状态机、规则、库存冲突、卖家链路这类约束型问题
- `Halley` 负责 App 与双端 UI/交互一致性
- `Aquinas` 负责支付、后端、部署、鉴权、链路完整性
- 主代理负责小程序具体改动、三方结果集成和最终验收

## 3. 各工位交付物

### 3.1 产品需求工位

目标：

- 把“科研仪器租赁与交易平台”定义清楚
- 明确 MVP 范围，不让支付、库存、纠纷在后期返工

交付物：

- PRD 摘要
- 角色清单
- 核心流程图
- 状态机
- 异常场景列表
- 字段与页面清单

绑定到当前项目的核查对象：

- 小程序页面：`/pages/home`、`/pages/category`、`/pages/equipment-detail`、`/pages/order-*`
- App 页面：`/app/pages/home`、`/app/pages/order-*`
- 云函数 action：`getInstruments`、`createOrder`、`confirmPayment`、`createDispute`

### 3.2 UI/交互工位

目标：

- 保证首页风格统一到所有关键页面
- 保证交易关键页的视觉层级和信息优先级正确

交付物：

- 页面路由图
- 页面线框层级说明
- 页面状态流说明
- 视觉不一致清单

绑定到当前项目的核查对象：

- 小程序：首页、分类、详情、订单列表、认证页、管理员三页
- App：首页、社区、项目、订单、认证、底部导航

### 3.3 小程序前端工位

目标：

- 把小程序跑通为真实业务前端，而不是只停留在演示页面

交付物：

- 页面实现
- 表单校验
- loading / empty / error
- 云函数 API 接入
- 管理端页面

主文件范围：

- `/pages/*`
- `/custom-tab-bar/*`
- `/utils/api.js`
- `/app.json`
- `/app.wxss`

### 3.4 App 前端工位

目标：

- 保证 App 和小程序界面、字段、链路口径一致

交付物：

- `uni-app` 页面实现
- 状态同步
- 协议页、支付页、认证页、订单页与小程序口径对齐

主文件范围：

- `/app/pages/*`
- `/app/components/*`
- `/app/common/service.js`
- `/app/common/payment.js`
- `/app/pages.json`

### 3.5 后端领域工位

目标：

- 把后端从“能读写”提升为“有规则的交易系统”

交付物：

- 领域模型
- API 契约
- 鉴权约束
- 状态流转约束
- 管理端接口

主文件范围：

- `/cloudfunctions/gateway/cloud-db.js`
- `/cloudfunctions/gateway/index.js`
- `/cloudfunctions/gateway/seed-data.js`
- `/cloudfunctions/bootstrap/*`

### 3.6 库存与规则工位

目标：

- 保证同一台仪器在同一时间段不会超卖
- 保证取消、超时、延期、归还都能回写库存

交付物：

- 仪器库存模型
- 可租日期规则
- 时间冲突判断
- 幂等与锁策略

当前代码里重点关注函数：

- `getOrderPreview`
- `createOrder`
- `confirmPayment`
- `getOrderList`
- `getOrderDetail`

### 3.7 支付与通知工位

目标：

- 让“下单 -> 支付 -> 回调 -> 通知 -> 履约”成为闭环

交付物：

- 支付下单参数定义
- 回调幂等方案
- 退款方案
- 到期提醒 / 客服介入 / 订单异常通知

当前代码里重点关注文件：

- `/cloudfunctions/gateway/cloud-db.js`
- `/app/common/payment.js`
- `/app/common/env.js`
- `/pages/order-payment/*`
- `/app/pages/order-payment/*`

### 3.8 测试与运维工位

目标：

- 把项目从“能跑”推进到“可持续上线”

交付物：

- 冒烟测试清单
- 回归清单
- 环境清单
- 数据初始化清单
- 发布回滚清单

主文件范围：

- `/docs/*`
- `/setup-cloud.ps1`
- 小程序/云函数/App 的构建与配置文件

## 4. 当前项目的角色与业务边界

### 4.1 角色

- 普通用户：浏览、收藏、聊天、下单、支付、发起纠纷、评价
- 认证用户：可发布仪器，可作为卖家/出租方接单
- 管理员：审核认证、维护学校学院、处理举报、处理纠纷
- 平台客服：介入争议、协调履约、推进退款/赔付

### 4.2 当前仓库已覆盖的角色能力

- 普通用户：基本可用
- 认证用户：发布仪器可用，但卖家侧订单和聊天链路还不完整
- 管理员：审核、举报、纠纷页面已存在
- 客服：有“介入”入口，但未形成独立客服工作台

### 4.3 MVP 边界

第一阶段必须稳定的闭环：

1. 浏览仪器
2. 查看详情
3. 认证申请
4. 发布仪器
5. 加购物车 / 直接下单
6. 支付
7. 查看订单
8. 聊天沟通
9. 发起纠纷 / 评价
10. 管理端审核认证与处理违规

第二阶段再进入：

- 优惠券
- 信用免押
- 多门店 / 多实验室
- 自动化赔损评估
- 智能推荐

## 5. 当前项目的状态机基线

### 5.1 仪器状态机

建议状态：

- `draft`：草稿
- `pending_review`：待审核
- `available`：可租 / 可售
- `reserved`：已预订待支付
- `scheduled`：已支付待交付
- `in_use`：租赁中 / 使用中
- `maintenance`：维修中
- `disabled`：停用
- `sold_out`：已售出

当前代码问题：

- 仪器更多是“展示对象”，还不是完整库存对象
- 缺少“设备编号级”的库存视角
- 缺少“同一时间段不可重叠”的日历化冲突模型

### 5.2 订单状态机

建议状态：

- `pending_payment`
- `pending_review`
- `pending_delivery`
- `active`
- `pending_return`
- `completed`
- `cancelled`
- `closed_abnormal`
- `dispute_open`
- `refund_processing`
- `refunded`

当前代码问题：

- 订单状态仍偏演示型，状态文案与业务含义未完全解耦
- 卖家视角订单查询不完整
- 远程实验咨询订单与普通仪器订单混在同一结构里，缺少统一的业务类型字段

### 5.3 支付状态机

建议状态：

- `unpaid`
- `paying`
- `paid`
- `refund_pending`
- `partially_refunded`
- `refunded`
- `payment_failed`

当前代码问题：

- 小程序后端 `getPaymentInfo` 还不是正式签名支付参数
- `confirmPayment` 仍是前端驱动的状态推进，不是真正的支付回调闭环
- App 仍默认 mock 支付

### 5.4 认证状态机

建议状态：

- `unverified`
- `pending`
- `approved`
- `rejected`
- `expired`

当前代码问题：

- 小程序已修掉“新用户自动认证”
- App 端仍有默认 mock 已认证用户的问题
- 认证资料目前缺少有效期与驳回原因字段

### 5.5 纠纷状态机

建议状态：

- `open`
- `processing`
- `awaiting_evidence`
- `awaiting_platform`
- `resolved_refund`
- `resolved_partial_refund`
- `resolved_repair`
- `rejected`
- `closed`

当前代码问题：

- 已有纠纷记录与处理页，但证据链字段不足
- 赔付、维修、保险、责任归属还没有结构化字段

## 6. API 契约建议

### 6.1 当前 action 现状

当前项目主要通过单一网关 action 分发：

- 内容与首页：`getHomeData` `getCategories` `getInstruments` `getInstrumentDetail`
- 用户与认证：`getProfile` `getSchoolOptions` `submitCertification`
- 收藏与购物车：`toggleFavorite` `getFavoriteList` `addToCart` `removeCartItem` `getCart`
- 订单：`getOrderPreview` `createOrder` `getPaymentInfo` `confirmPayment` `getOrderList` `getOrderDetail`
- 聊天：`ensureInstrumentChat` `getChatList` `getChatDetail` `sendChatMessage` `requestSupportIntervention`
- 发布与管理：`publishInstrument` `updateInstrument` `getMyInstruments`
- 风控：`createDispute` `submitReport` `publishRating`
- 管理端：`getAdminDashboard` `getSchoolList` `addSchool` `getCertificationList` `reviewCertification` `getReportList` `resolveReport` `getDisputeList` `resolveDispute`

### 6.2 推荐 API 分组

建议逐步从“单 action 网关”过渡到“领域分组”：

- `/auth/*`
- `/profiles/*`
- `/schools/*`
- `/instruments/*`
- `/inventory/*`
- `/orders/*`
- `/payments/*`
- `/chats/*`
- `/certifications/*`
- `/ratings/*`
- `/reports/*`
- `/disputes/*`
- `/admin/*`

### 6.3 关键字段建议

#### instruments

- `id`
- `ownerUserId`
- `sellerType`
- `deviceCode`
- `categoryId`
- `tradeModes`
- `defaultTradeMode`
- `dailyPrice`
- `salePrice`
- `depositRule`
- `insuranceRule`
- `precisionSpec`
- `disciplineTags`
- `supportsRemote`
- `includesDataCode`
- `status`
- `reviewStatus`

#### inventory_units

- `id`
- `instrumentId`
- `unitCode`
- `status`
- `location`
- `calendarLocks`

#### orders

- `id`
- `orderType`
- `instrumentId`
- `inventoryUnitId`
- `buyerUserId`
- `sellerUserId`
- `tradeMode`
- `startDate`
- `endDate`
- `rentDays`
- `pricingSnapshot`
- `depositAmount`
- `insuranceAmount`
- `serviceFee`
- `paymentStatus`
- `orderStatus`
- `agreementVersion`
- `deliveryType`
- `supportStatus`
- `createdAt`

#### payments

- `id`
- `orderId`
- `paymentChannel`
- `merchantOrderNo`
- `transactionId`
- `payStatus`
- `callbackStatus`
- `callbackRaw`
- `refundStatus`

#### certifications

- `id`
- `userId`
- `name`
- `phone`
- `school`
- `college`
- `proofFiles`
- `status`
- `reviewRemark`
- `approvedAt`
- `expiredAt`

#### disputes

- `id`
- `orderId`
- `userId`
- `reasonCode`
- `description`
- `evidenceFiles`
- `status`
- `resolutionType`
- `compensationAmount`
- `operatorId`

## 7. 串联角色的执行顺序

### 阶段 1：总控与产品

输出：

- MVP 范围
- 状态机基线
- 字段口径
- API 契约基线

验收：

- 前后端对“字段、状态、角色、异常”的理解一致

### 阶段 2：后端领域 + 库存规则

输出：

- 真实订单状态机
- 卖家 / 买家 / 管理员权限约束
- 可租时间与库存冲突规则
- 支付幂等接口口径

验收：

- 不出现同一时间段重复租赁
- 不出现前端直接越权改订单

### 阶段 3：UI/交互

输出：

- 页面层级和组件规范
- 首页风格统一方案

验收：

- 首页、详情、订单、认证、后台页视觉一致

### 阶段 4：前端实现

输出：

- 小程序和 App 的页面联调
- 所有关键页有三态
- 协议、认证、订单、聊天闭环可跑

验收：

- 小程序与 App 字段、状态、按钮口径一致

### 阶段 5：支付与通知

输出：

- 支付发起
- 支付回调
- 退款
- 到期提醒 / 纠纷提醒 / 管理员通知

验收：

- 不依赖前端手工改状态

### 阶段 6：测试与运维

输出：

- 冒烟清单
- 回归清单
- 环境配置
- 上线阻塞清单

验收：

- 真实云环境可重复部署、可重复初始化、可回滚

## 8. 统一输入输出模板

### 8.1 输入模板

- 当前模块目标
- 上游依赖
- 已确认接口
- 未决问题
- 验收标准

### 8.2 输出模板

- 本轮产出
- 涉及文件
- 风险点
- 需下游配合事项
- 阻塞项

## 9. 推荐提示词模板

### 9.1 产品需求子代理

你负责本项目的产品定义。请基于当前仓库里的小程序、App、云函数和真实集合，输出本轮功能的角色、流程、状态机、异常链路和字段口径。不要空谈方法论，要指出当前代码与产品定义不一致的地方，并给出下一步需要后端和前端对齐的字段与状态。

### 9.2 UI/交互子代理

你负责本项目的体验审校。请只关注信息架构、页面层级、状态表达、视觉一致性和按钮优先级。重点检查首页风格是否延续到订单、认证、后台、社区、项目、消息和收藏页。输出问题、优先级、改法和涉及文件。

### 9.3 后端领域子代理

你负责本项目的后端业务规则。请结合当前 `cloudfunctions/gateway/cloud-db.js`、现有集合和页面链路，检查订单、认证、收藏、购物车、聊天、举报、纠纷、管理后台的权限和状态流转。输出高风险问题、建议状态机、字段补充和必须加的鉴权点。

### 9.4 库存与规则子代理

你负责本项目的库存和交易一致性。请围绕仪器库存、可租日期、订单创建、支付超时、取消订单、延期、提前归还、保险、押金和赔损，给出当前代码缺口和建议规则。输出数据模型、冲突判断逻辑和幂等策略。

### 9.5 前端子代理

你负责本项目的小程序或 App 前端实现。请在不改动跨域契约的前提下，修复页面逻辑、表单校验、状态三态和视觉一致性。输出具体文件、交互变化、未覆盖场景和需要后端配合的点。

### 9.6 支付与通知子代理

你负责本项目的支付与消息。请结合小程序支付页、App 支付页、云函数支付口径和订单状态机，检查支付参数、回调、退款、幂等、通知和超时释放库存。输出支付链路图、接口建议、回调字段和风险点。

### 9.7 测试与运维子代理

你负责本项目的测试和上线。请给出真实云环境、小程序前端、App 工程、支付链路、数据初始化、日志追踪、回滚方案的测试矩阵和上线阻塞项。输出必须补的脚本、文档、日志点和环境差异。

## 10. 当前最优先的联动任务

1. 修复卖家侧订单 / 聊天视角缺失
2. 修复协议页缺少 `instrumentId` 透传
3. 修复远程实验订单在订单列表中的空标题
4. 修复 App 默认 mock 已认证用户和默认 mock 支付
5. 补齐 App 认证页 picker 回填、购物车去重、详情空态
6. 统一管理员页、订单页、社区页、项目页的视觉风格
7. 明确真实支付回调、库存锁定和退款释放库存方案

