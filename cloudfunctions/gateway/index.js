const cloud = require('wx-server-sdk');

cloud.init({
  env: cloud.DYNAMIC_CURRENT_ENV
});

const schools = [
  {
    id: 'sch-001',
    name: '中国海洋大学',
    colleges: ['海洋地球科学学院', '海洋与大气学院', '信息科学与工程学部']
  },
  {
    id: 'sch-002',
    name: '山东大学',
    colleges: ['海洋学院', '环境科学与工程学院', '控制科学与工程学院']
  },
  {
    id: 'sch-003',
    name: '中国石油大学（华东）',
    colleges: ['地球科学与技术学院', '化学化工学院', '机电工程学院']
  }
];

const instrumentCategories = ['全部', '海洋监测', '地质分析', '材料实验', '光学测试', '环境检测'];

const instruments = [
  {
    id: 'ins-001',
    name: '多参数海水水质分析仪',
    category: '海洋监测',
    price: 680,
    priceLabel: '680 元 / 天',
    location: '青岛',
    sellerId: 'u-001',
    sellerName: '司艳文',
    school: '中国海洋大学',
    college: '海洋地球科学学院',
    verified: true,
    phone: '13800138000',
    desc: '适用于近岸海域水质监测与海洋调查，支持温度、盐度、浊度等多参数检测。',
    tags: ['已认证', '支持租赁', '可议价'],
    stock: 1,
    condition: '九成新',
    publishStatus: '已上架'
  },
  {
    id: 'ins-002',
    name: '岩芯薄片扫描仪',
    category: '地质分析',
    price: 880,
    priceLabel: '880 元 / 天',
    location: '烟台',
    sellerId: 'u-002',
    sellerName: '王海宁',
    school: '中国石油大学（华东）',
    college: '地球科学与技术学院',
    verified: true,
    phone: '13900139000',
    desc: '面向岩芯薄片观察与数据归档，适合矿物结构判读与沉积研究。',
    tags: ['已认证', '支持租赁'],
    stock: 1,
    condition: '八成新',
    publishStatus: '已上架'
  },
  {
    id: 'ins-003',
    name: '紫外可见分光光度计',
    category: '光学测试',
    price: 420,
    priceLabel: '420 元 / 天',
    location: '济南',
    sellerId: 'u-003',
    sellerName: '李卓',
    school: '山东大学',
    college: '环境科学与工程学院',
    verified: true,
    phone: '13700137000',
    desc: '适用于常规吸光度测量和实验室化学分析，带标准校准附件。',
    tags: ['已认证', '支持购买'],
    stock: 1,
    condition: '九五新',
    publishStatus: '已上架'
  },
  {
    id: 'ins-004',
    name: '便携式重金属检测仪',
    category: '环境检测',
    price: 560,
    priceLabel: '560 元 / 天',
    location: '青岛',
    sellerId: 'u-001',
    sellerName: '司艳文',
    school: '中国海洋大学',
    college: '海洋与大气学院',
    verified: true,
    phone: '13800138000',
    desc: '用于海水、土壤和沉积物重金属检测，适合现场快速筛查。',
    tags: ['已认证', '支持租赁', '热门'],
    stock: 1,
    condition: '九成新',
    publishStatus: '已上架'
  }
];

const favorites = ['ins-001', 'ins-003'];
const cartItems = [{ id: 'cart-001', instrumentId: 'ins-002', quantity: 1 }];
const chats = [
  { id: 'chat-001', sellerName: '王海宁', instrumentName: '岩芯薄片扫描仪', lastMessage: '明天上午可以现场看设备。', updatedAt: '10:26' },
  { id: 'chat-002', sellerName: '李卓', instrumentName: '紫外可见分光光度计', lastMessage: '如果直接购买可以走校内转账。', updatedAt: '昨天' }
];
const chatMessages = {
  'chat-001': [
    { from: 'seller', text: '你好，设备目前可租。', time: '10:12' },
    { from: 'buyer', text: '本周能否先看一下设备状态？', time: '10:18' },
    { from: 'seller', text: '明天上午可以现场看设备。', time: '10:26' }
  ],
  'chat-002': [
    { from: 'buyer', text: '请问支持购买吗？', time: '昨天 14:05' },
    { from: 'seller', text: '支持，如果直接购买可以走校内转账。', time: '昨天 14:20' }
  ]
};
const ratings = [{ id: 'rate-001', orderId: 'ord-20260318-004', target: '便携式重金属检测仪', score: 5, content: '沟通顺畅，设备状态和描述一致。' }];
const orders = [
  { id: 'ord-20260319-001', instrumentId: 'ins-002', buyerName: '司艳文', sellerName: '王海宁', amount: 880, status: '待付款', createdAt: '2026-03-19 09:30' },
  { id: 'ord-20260318-004', instrumentId: 'ins-004', buyerName: '司艳文', sellerName: '司艳文', amount: 560, status: '已完成', createdAt: '2026-03-18 17:20' }
];

function getInstrumentById(id) {
  return instruments.find((item) => item.id === id) || instruments[0];
}

function getOrderById(id) {
  return orders.find((item) => item.id === id) || orders[0];
}

function getCartDetail() {
  const list = cartItems.map((item) => {
    const instrument = getInstrumentById(item.instrumentId);
    return { ...item, instrument, subtotal: instrument.price * item.quantity };
  });
  return {
    list,
    total: list.reduce((sum, item) => sum + item.subtotal, 0)
  };
}

exports.main = async (event) => {
  const { action, payload = {} } = event;

  switch (action) {
    case 'getHomeData':
      return {
        hero: {
          title: '神经突触仪器共享平台',
          subtitle: '已认证个人用户可发布与购买仪器，管理者负责认证审核、院校维护与交易秩序管理。'
        },
        quickEntries: [
          { title: '全部分类', page: '/pages/category/index', desc: '按仪器类型浏览' },
          { title: '认证中心', page: '/pages/certification/index', desc: '填写姓名、电话与院校' },
          { title: '发布仪器', page: '/pages/instrument-publish/index', desc: '认证后发布个人设备' },
          { title: '管理后台', page: '/pages/admin/index', desc: '学校学院与审核维护' }
        ],
        roleCards: [
          { title: '已认证个人用户', desc: '认证后兼具买家和卖家双重身份，可发布个人仪器，也能浏览并购买他人发布的仪器。' },
          { title: '管理者 / 平台方', desc: '负责学校学院维护、用户认证审核、违规信息处理和交易纠纷协调。' }
        ],
        featuredInstruments: instruments.slice(0, 3),
        stats: [
          { label: '认证院校', value: `${schools.length} 所` },
          { label: '在架仪器', value: `${instruments.length} 台` },
          { label: '待审核认证', value: '6 条' }
        ]
      };
    case 'getCategories':
      return { categories: instrumentCategories, schools };
    case 'getInstruments': {
      const keyword = (payload.keyword || '').trim();
      const category = payload.category || '全部';
      return {
        categories: instrumentCategories,
        list: instruments.filter((item) => {
          const categoryMatched = category === '全部' || item.category === category;
          const keywordMatched =
            !keyword ||
            item.name.includes(keyword) ||
            item.school.includes(keyword) ||
            item.college.includes(keyword) ||
            item.tags.some((tag) => tag.includes(keyword));
          return categoryMatched && keywordMatched;
        })
      };
    }
    case 'getInstrumentDetail': {
      const instrument = getInstrumentById(payload.id);
      return {
        instrument,
        isFavorite: favorites.includes(instrument.id),
        recommendations: instruments.filter((item) => item.id !== instrument.id).slice(0, 2)
      };
    }
    case 'getCart':
      return getCartDetail();
    case 'addToCart':
      return { success: true, message: '已加入购物车' };
    case 'getOrderPreview':
      return {
        ...getCartDetail(),
        contactName: '司艳文',
        contactPhone: '13800138000'
      };
    case 'createOrder':
      return { success: true, orderId: 'ord-20260319-099', amount: getCartDetail().total };
    case 'getPaymentInfo':
      return { order: getOrderById(payload.orderId || orders[0].id) };
    case 'confirmPayment':
      return { success: true, orderId: payload.orderId || orders[0].id };
    case 'getChatList':
      return { list: chats };
    case 'getChatDetail':
      return {
        chat: chats.find((item) => item.id === payload.id) || chats[0],
        messages: chatMessages[payload.id] || chatMessages['chat-001']
      };
    case 'getProfile':
      return {
        certification: {
          status: '已认证',
          name: '司艳文',
          phone: '13800138000',
          school: '中国海洋大学',
          college: '海洋地球科学学院'
        },
        orderCount: orders.length,
        favoriteCount: favorites.length,
        instrumentCount: instruments.filter((item) => item.sellerId === 'u-001').length
      };
    case 'getSchoolOptions':
      return schools;
    case 'submitCertification':
      return { success: true, status: '待审核', message: '认证信息已提交，管理员审核通过后即可发布仪器。' };
    case 'getMyInstruments':
      return { list: instruments.filter((item) => item.sellerId === 'u-001') };
    case 'publishInstrument':
      return { success: true, instrumentId: `ins-${Date.now()}`, message: '仪器发布成功，当前为演示环境，默认直接上架。' };
    case 'getInstrumentEditDetail':
      return { instrument: getInstrumentById(payload.id) };
    case 'updateInstrument':
      return { success: true, message: '仪器信息已更新' };
    case 'getOrderList':
      return { list: orders.map((item) => ({ ...item, instrument: getInstrumentById(item.instrumentId) })) };
    case 'getOrderDetail': {
      const order = getOrderById(payload.id);
      return { order, instrument: getInstrumentById(order.instrumentId) };
    }
    case 'getFavoriteList':
      return { list: instruments.filter((item) => favorites.includes(item.id)) };
    case 'getRatingList':
      return { list: ratings };
    case 'publishRating':
      return { success: true, message: '评价已提交' };
    case 'getAdminDashboard':
      return {
        pendingCertification: 6,
        totalSchools: schools.length,
        totalInstruments: instruments.length,
        openDisputes: 1
      };
    case 'getSchoolList':
      return { list: schools };
    case 'addSchool':
      return { success: true, message: '学校 / 学院信息已添加' };
    default:
      return { success: false, message: `未知动作：${action}` };
  }
};
