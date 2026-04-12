import env from './env'

const STORE_KEY = 'synaptic-app-store'
const LEGACY_SEED_PHONE = '13800138000'

function createEmptyCertification() {
  return {
    name: '',
    role: '科研工作者',
    phone: '',
    email: '',
    instituteId: '',
    school: '',
    college: '',
    proofName: '',
    status: '未认证',
    pendingMessage: '完成认证后才可发布仪器、加入购物车、下单和发起纠纷。'
  }
}

function createGuestUser() {
  return {
    id: 'u-app-guest',
    isAdmin: false,
    certification: createEmptyCertification()
  }
}

const SEED = {
  user: createGuestUser(),
  schools: [
    { id: 'sch-001', name: '中国海洋大学', colleges: ['海洋地球科学学院', '海洋与大气学院', '信息科学与工程学部'] },
    { id: 'sch-002', name: '中国石油大学（华东）', colleges: ['地球科学与技术学院', '机电工程学院', '控制科学与工程学院'] },
    { id: 'sch-003', name: '山东大学', colleges: ['环境科学与工程学院', '海洋学院', '材料科学与工程学院'] }
  ],
  categories: ['全部', '海洋观测', '地质灾害', '生物材料', '化学分析', '高精仪器'],
  instruments: [
    {
      id: 'ins-001',
      name: '波浪作用下沉积物孔压响应模拟装置',
      category: '海洋观测',
      sellerId: 'u-101',
      sellerName: '杜星 教授团队',
      sellerRole: '高校教师',
      school: '中国海洋大学',
      college: '海洋地球科学学院',
      verifiedType: 'blue',
      avatarClass: 'a1',
      posterTheme: 'poster-theme-1',
      location: '青岛市 · 崂山区',
      phone: '13800138011',
      price: 300,
      salePrice: 6800,
      tradeModes: ['租赁', '出售'],
      defaultTradeMode: '租赁',
      deposit: 1200,
      platformServiceFee: 24,
      desc: '可高精度预测波浪引起的孔隙水压力，适用于海洋灾害模拟与地质时间序列分析。',
      precision: '误差小于 2 kPa',
      disciplines: ['海洋灾害', '沉积动力学', '岩土工程'],
      withDataPackage: true,
      remote: true,
      supportInsurance: true,
      availableDates: ['2026-03-21', '2026-03-22', '2026-03-23', '2026-03-24', '2026-03-25'],
      tags: ['远程实验', '附带代码', '教师团队'],
      condition: '实验室在役',
      publishStatus: '已上架',
      servicePackage: '附带标准数据集与处理代码',
      breachRules: ['超时归还按日租金 10% 收取违约金', '无故取消订单将扣除平台服务费'],
      damageRules: ['人为损坏按维修报价赔付', '参数漂移需承担校准成本']
    },
    {
      id: 'ins-002',
      name: '高精度微结构表征系统',
      category: '高精仪器',
      sellerId: 'u-102',
      sellerName: '刘海洋',
      sellerRole: '仪器供应方',
      school: '山东大学',
      college: '材料科学与工程学院',
      verifiedType: 'green',
      avatarClass: 'a2',
      posterTheme: 'poster-theme-2',
      location: '济南市 · 中心校区',
      phone: '13988887777',
      price: 580,
      salePrice: 16800,
      tradeModes: ['租赁', '出售'],
      defaultTradeMode: '租赁',
      deposit: 3000,
      platformServiceFee: 40,
      desc: '适用于高分子材料、生物材料和微纳结构样品的精细表征与图像采集。',
      precision: '分辨率 0.01 μm',
      disciplines: ['生物材料', '材料表征'],
      withDataPackage: true,
      remote: false,
      supportInsurance: true,
      availableDates: ['2026-03-22', '2026-03-23', '2026-03-24', '2026-03-25', '2026-03-26'],
      tags: ['高精仪器', '图像采集'],
      condition: '已校准',
      publishStatus: '已上架',
      servicePackage: '提供标准表征报告与图像导出',
      breachRules: ['预约排期前 24 小时内取消需支付排期成本'],
      damageRules: ['异常操作导致的部件损坏由承租方承担维修费用']
    }
  ],
  favorites: [],
  cartItems: [],
  chats: [],
  chatMessages: {},
  orders: [],
  posts: [
    {
      id: 'post-001',
      title: '海洋观测仪器跨校共享的排期经验',
      tag: '仪器共享',
      author: '司艳文',
      excerpt: '从认证、预约到数据交付，把跨校共享里最容易踩坑的节点梳理成了标准流程。',
      content: '跨校共享里真正影响效率的不是设备本身，而是排期、交接记录和数据包标准。建议平台在下单前同步实验目的、样本量和交付格式。',
      likes: 36,
      comments: 12
    },
    {
      id: 'post-002',
      title: '高精仪器租赁里为什么保险必须前置',
      tag: '风控讨论',
      author: '王海宁',
      excerpt: '高精度设备的争议，常常不在损坏，而在参数漂移和责任归属。',
      content: '对于高精仪器，平台应要求发布方在上架时提交最近一次校准时间、误差范围和损坏责任说明。',
      likes: 28,
      comments: 9
    }
  ],
  projects: [
    {
      id: 'proj-001',
      title: '海岸带风暴潮实验平台联合验证',
      owner: '青岛某海洋科技企业',
      domain: '海洋观测',
      status: '招募中',
      intro: '寻找具备波浪水槽、孔压采集与数据反演经验的高校团队，共同完成风暴潮场景验证。',
      budget: '8万 - 15万',
      duration: '8 周',
      keywords: ['风暴潮', '波浪水槽', '数据反演'],
      targetRoles: ['高校教师', '科研工作者', '仪器供应方'],
      evaluation: {
        hard: '重点看过往实验平台、论文成果、数据交付能力与排期稳定性。',
        soft: '重点看沟通效率、实验复盘质量与项目协作意识。'
      },
      matches: [{ name: '杜星 教授团队', title: '中国海洋大学 / 一海所', score: 96, tags: ['海洋灾害', '远程实验'] }],
      flow: ['提交需求', '平台初筛', '候选团队匹配', '沟通排期', '签署协议并执行'],
      matrix: [
        { label: '设备匹配度', value: '94%' },
        { label: '交付稳定性', value: '88%' },
        { label: '协作效率', value: '91%' }
      ]
    }
  ],
  aiTools: [
    { id: 'ai-001', name: '风暴潮风险评估', mode: '数据分析', subtitle: '用于海岸带灾害评估和实验结果预判。', outcome: '输出风险等级、关键变量和处理建议。' },
    { id: 'ai-002', name: '科研资源匹配', mode: '撮合推荐', subtitle: '根据项目需求推荐团队与设备。', outcome: '输出合作候选人和资源缺口。' }
  ],
  aiTasks: []
}

function clone(data) {
  return JSON.parse(JSON.stringify(data))
}

function normalizeState(rawState) {
  const next = rawState && typeof rawState === 'object' ? rawState : clone(SEED)
  if (
    !next.user ||
    (next.user.id === 'u-app-001' && next.user.isAdmin === true) ||
    (next.user.certification &&
      next.user.certification.phone === LEGACY_SEED_PHONE &&
      next.user.certification.status === '已认证')
  ) {
    next.user = createGuestUser()
    next.cartItems = []
    next.favorites = []
    next.orders = []
    next.chats = []
    next.chatMessages = {}
  }
  if (!next.user.certification) {
    next.user.certification = createEmptyCertification()
  }
  if (!Array.isArray(next.cartItems)) next.cartItems = []
  if (!Array.isArray(next.favorites)) next.favorites = []
  if (!Array.isArray(next.orders)) next.orders = []
  if (!Array.isArray(next.instruments)) next.instruments = []
  if (!Array.isArray(next.categories)) next.categories = []
  if (!Array.isArray(next.schools)) next.schools = []
  if (!Array.isArray(next.chats)) next.chats = []
  if (!next.chatMessages || typeof next.chatMessages !== 'object') next.chatMessages = {}
  return next
}

let state = normalizeState(uni.getStorageSync(STORE_KEY) || clone(SEED))

function persist() {
  uni.setStorageSync(STORE_KEY, state)
}

persist()

function labels(instrument) {
  return {
    ...instrument,
    priceLabel: `¥${instrument.price} /天`,
    salePriceLabel: instrument.salePrice ? `¥${instrument.salePrice} 买断` : '仅支持租赁'
  }
}

function getInstrument(id) {
  return state.instruments.find((item) => item.id === id)
}

function requireVerified(actionName) {
  if (!['已认证', '已通过'].includes(state.user.certification.status)) {
    throw new Error(`${actionName || '当前操作'}仅对已认证用户开放`)
  }
}

async function callRemote(action, payload) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: env.apiBaseUrl,
      method: 'POST',
      data: { action, payload },
      success: ({ data }) => resolve(data),
      fail: reject
    })
  })
}

export async function callService(action, payload = {}) {
  if (!env.useMock) {
    return callRemote(action, payload)
  }

  switch (action) {
    case 'getHomeData':
      return {
        hero: {
          title: '神经突触仪器租赁与学术交流',
          subtitle: '以高校认证、科研背书和仪器风控为核心，把租赁、远程实验、数据交付与学术沟通做成一条真实链路。'
        },
        stats: [
          { label: '认证院校', value: `${state.schools.length} 所` },
          { label: '在架仪器', value: `${state.instruments.length} 台` },
          { label: '活跃订单', value: `${state.orders.length} 笔` }
        ],
        featuredInstruments: clone(state.instruments.map(labels))
      }
    case 'getCategories':
      return { categories: clone(state.categories), schools: clone(state.schools.map((item) => ({ ...item, collegesText: item.colleges.join(' / ') }))) }
    case 'getInstruments': {
      const category = payload.category || '全部'
      const normalizedCategory = category === '全部推荐' ? '全部' : category
      const keyword = (payload.keyword || '').trim()
      return {
        categories: clone(state.categories),
        list: clone(
          state.instruments
            .filter((item) => normalizedCategory === '全部' || item.category === normalizedCategory)
            .filter((item) => !keyword || `${item.name}${item.sellerName}${item.school}${item.tags.join('')}`.includes(keyword))
            .map(labels)
        )
      }
    }
    case 'getInstrumentDetail':
      {
        const instrument = getInstrument(payload.id)
        return {
          instrument: instrument ? clone(labels(instrument)) : null,
          isFavorite: state.favorites.includes(payload.id),
          related: clone(state.instruments.filter((item) => item.id !== payload.id).slice(0, 2).map(labels))
        }
      }
    case 'toggleFavorite': {
      const index = state.favorites.indexOf(payload.id)
      if (index >= 0) state.favorites.splice(index, 1)
      else state.favorites.unshift(payload.id)
      persist()
      return { isFavorite: state.favorites.includes(payload.id) }
    }
    case 'getFavoriteList':
      return { list: clone(state.favorites.map((id) => labels(getInstrument(id))).filter(Boolean)) }
    case 'addToCart': {
      requireVerified('加入购物车')
      const tradeMode = payload.tradeMode || '租赁'
      const existed = state.cartItems.find(
        (item) => item.instrumentId === payload.instrumentId && item.tradeMode === tradeMode
      )
      if (!existed) {
        state.cartItems.unshift({
          id: `cart-${Date.now()}`,
          instrumentId: payload.instrumentId,
          tradeMode,
          startDate: payload.startDate || '',
          endDate: payload.endDate || ''
        })
        persist()
      }
      return { message: '已加入购物车' }
    }
    case 'getCart':
      return {
        list: clone(
          state.cartItems.map((item) => ({
            ...item,
            instrument: labels(getInstrument(item.instrumentId))
          }))
        )
      }
    case 'removeCartItem':
      state.cartItems = state.cartItems.filter((item) => item.id !== payload.id)
      persist()
      return { message: '已移出购物车' }
    case 'getOrderPreview': {
      const instrument = getInstrument(payload.instrumentId)
      const tradeMode = payload.tradeMode || instrument.defaultTradeMode
      const rentDays = tradeMode === '租赁' ? Math.max(1, Number(payload.rentDays || 1)) : 0
      const rentalAmount = tradeMode === '租赁' ? instrument.price * rentDays : 0
      const saleAmount = tradeMode === '出售' ? instrument.salePrice : 0
      const insuranceFee = payload.insuranceAccepted ? 24 : 0
      const total = rentalAmount + saleAmount + instrument.deposit + instrument.platformServiceFee + insuranceFee
      return {
        instrument: clone(labels(instrument)),
        tradeMode,
        rentDays,
        rentalAmount,
        saleAmount,
        insuranceFee,
        deposit: instrument.deposit,
        platformServiceFee: instrument.platformServiceFee,
        total
      }
    }
    case 'createOrder': {
      requireVerified('下单')
      const preview = await callService('getOrderPreview', payload)
      const instrument = getInstrument(payload.instrumentId)
      const id = `ord-${Date.now()}`
      state.orders.unshift({
        id,
        instrumentId: instrument.id,
        instrumentName: instrument.name,
        buyerName: state.user.certification.name || '未认证用户',
        sellerName: instrument.sellerName,
        tradeMode: preview.tradeMode,
        status: '待支付',
        startDate: payload.startDate || instrument.availableDates[0],
        endDate: payload.endDate || instrument.availableDates[1] || instrument.availableDates[0],
        rentDays: preview.rentDays,
        amount: preview.total,
        total: preview.total,
        rentalAmount: preview.rentalAmount,
        saleAmount: preview.saleAmount,
        insuranceFee: preview.insuranceFee,
        deposit: preview.deposit,
        platformServiceFee: preview.platformServiceFee,
        createdAt: new Date().toLocaleString(),
        agreementTitle: '科研仪器租赁与数据交付协议'
      })
      state.cartItems = state.cartItems.filter(
        (item) => !(item.instrumentId === instrument.id && item.tradeMode === preview.tradeMode)
      )
      persist()
      return { orderId: id, orderNo: id, message: '订单已创建' }
    }
    case 'getPaymentInfo': {
      const order = state.orders.find((item) => item.id === payload.orderId)
      return {
        orderId: payload.orderId,
        provider: '',
        orderInfo: '',
        mode: env.paymentMode,
        amount: order ? order.total : 0
      }
    }
    case 'confirmPayment': {
      const order = state.orders.find((item) => item.id === payload.orderId)
      if (order) order.status = '已支付待排期'
      persist()
      return { message: '支付成功', orderId: payload.orderId }
    }
    case 'getOrderList':
      return { list: clone(state.orders) }
    case 'getOrderDetail': {
      const order = state.orders.find((item) => item.id === payload.id)
      return { order: clone(order), instrument: order && order.instrumentId ? clone(labels(getInstrument(order.instrumentId))) : null }
    }
    case 'ensureInstrumentChat': {
      requireVerified('联系发布方')
      let chat = state.chats.find((item) => item.instrumentId === payload.instrumentId)
      if (!chat) {
        const instrument = getInstrument(payload.instrumentId)
        chat = {
          id: `chat-${Date.now()}`,
          instrumentId: instrument.id,
          sellerName: instrument.sellerName,
          sellerRole: instrument.sellerRole,
          instrumentName: instrument.name,
          updatedAt: new Date().toLocaleString(),
          supportIntervened: false
        }
        state.chats.unshift(chat)
        state.chatMessages[chat.id] = [{ from: 'system', text: '会话已创建，可在此确认参数、保险和交付方式。', time: '刚刚' }]
        persist()
      }
      return { chatId: chat.id }
    }
    case 'getChatList':
      return {
        list: clone(
          state.chats.map((chat) => {
            const list = state.chatMessages[chat.id] || []
            const last = list[list.length - 1]
            return {
              ...chat,
              lastMessage: last ? last.text : '暂无消息'
            }
          })
        )
      }
    case 'getChatDetail':
      return { chat: clone(state.chats.find((item) => item.id === payload.id)), messages: clone(state.chatMessages[payload.id] || []) }
    case 'sendChatMessage': {
      const list = state.chatMessages[payload.chatId] || []
      list.push({ from: 'buyer', text: payload.text, time: '刚刚' })
      state.chatMessages[payload.chatId] = list
      const chat = state.chats.find((item) => item.id === payload.chatId)
      if (chat) chat.updatedAt = new Date().toLocaleString()
      persist()
      return { message: '发送成功' }
    }
    case 'requestSupportIntervention': {
      const chat = state.chats.find((item) => item.id === payload.chatId)
      if (chat) chat.supportIntervened = true
      ;(state.chatMessages[payload.chatId] || []).push({ from: 'system', text: '平台客服已介入，请继续补充争议情况与凭证。', time: '刚刚' })
      persist()
      return { message: '平台已介入' }
    }
    case 'getProfile':
      return {
        certification: clone(state.user.certification),
        instrumentCount: state.instruments.filter((item) => item.sellerId === state.user.id).length,
        orderCount: state.orders.length,
        favoriteCount: state.favorites.length,
        isAdmin: state.user.isAdmin
      }
    case 'submitCertification':
      state.user.certification = {
        ...state.user.certification,
        ...payload,
        status: '待审核',
        pendingMessage: '认证资料已提交，等待平台审核。'
      }
      persist()
      return { message: '认证已提交' }
    case 'resetCertification':
      state.user.certification = {
        name: '',
        role: '科研工作者',
        phone: '',
        email: '',
        instituteId: '',
        school: '',
        college: '',
        proofName: '',
        status: '未认证',
        pendingMessage: '完成认证后才能解锁发布、下单和争议处理能力。'
      }
      persist()
      return { message: '已重置为未认证' }
    case 'publishInstrument': {
      requireVerified('发布仪器')
      const editing = payload.id ? getInstrument(payload.id) : null
      const record = {
        ...(editing || {
          id: payload.id || `ins-${Date.now()}`,
          sellerId: state.user.id,
          verifiedType: 'blue',
          avatarClass: 'a1',
          posterTheme: 'poster-theme-3',
          publishStatus: '已上架',
          availableDates: ['2026-03-24', '2026-03-25', '2026-03-26', '2026-03-27']
        }),
        ...payload,
        sellerId: state.user.id,
        sellerName: state.user.certification.name || '未认证用户',
        sellerRole: state.user.certification.role || '科研工作者',
        school: state.user.certification.school || '待认证学校',
        college: state.user.certification.college || '待认证学院'
      }
      if (editing) {
        state.instruments = state.instruments.map((item) => (item.id === editing.id ? record : item))
      } else {
        state.instruments.unshift(record)
      }
      persist()
      return { message: editing ? '仪器已更新' : '仪器已发布', id: record.id }
    }
    case 'getMyInstruments':
      return { list: clone(state.instruments.filter((item) => item.sellerId === state.user.id).map(labels)) }
    case 'getCommunity':
      return { tags: ['全部', '仪器共享', '风控讨论'], list: clone(state.posts) }
    case 'getPostDetail': {
      const post = state.posts.find((item) => item.id === payload.id)
      return { post: post ? clone(post) : null, related: clone(state.posts.filter((item) => item.id !== payload.id)) }
    }
    case 'getProjects':
      return { filters: ['全部', '海洋观测', '高精仪器'], list: clone(state.projects) }
    case 'getProjectDetail': {
      const project = state.projects.find((item) => item.id === payload.id)
      return {
        project: project ? clone(project) : null,
        flow: clone((project && project.flow) || []),
        matrix: clone((project && project.matrix) || [])
      }
    }
    case 'getAiTools':
      return { tools: clone(state.aiTools) }
    case 'submitAiTask': {
      const tool = state.aiTools.find((item) => item.id === payload.toolId) || state.aiTools[0]
      const result = {
        toolName: tool.name,
        summary: `系统已围绕“${payload.goal}”生成首轮分析建议，并把结果结构化沉淀为可继续追踪的任务。`,
        metrics: [
          { label: '风险等级', value: '中高' },
          { label: '关键变量', value: '4 项' },
          { label: '建议动作', value: '3 条' }
        ],
        insights: ['建议优先补充缺失的样本说明和实验边界条件。', '当前数据可支持首轮趋势判断，但还不适合直接做最终结论。']
      }
      state.aiTasks.unshift({ id: `ai-task-${Date.now()}`, ...result })
      persist()
      return result
    }
    case 'createRemoteOrder': {
      requireVerified('提交远程实验需求')
      const id = `ord-${Date.now()}`
      state.orders.unshift({
        id,
        instrumentId: '',
        instrumentName: payload.topic,
        buyerName: state.user.certification.name || '未认证用户',
        sellerName: '平台远程实验服务组',
        tradeMode: '远程实验咨询',
        status: '待确认',
        contact: payload.contact,
        amount: 0,
        total: 0,
        rentalAmount: 0,
        saleAmount: 0,
        insuranceFee: 0,
        deposit: 0,
        platformServiceFee: 0,
        createdAt: new Date().toLocaleString(),
        agreementTitle: '科研仪器租赁与数据交付协议'
      })
      persist()
      return { message: '远程实验需求已提交', orderNo: id, orderId: id }
    }
    case 'getAgreementContent':
      return {
        title: '科研仪器租赁与数据交付协议',
        version: 'v1.2',
        summary: '覆盖租赁周期、押金要求、违约规则、设备损坏责任和数据交付说明。',
        items: ['租赁前需完成实名认证与机构认证。', '押金在设备按期归还后原路退回。', '保险开启后可覆盖约定范围内的运输与维修风险。', '争议将基于聊天记录、验货记录与协议条款协调处理。']
      }
    default:
      return { success: true }
  }
}
