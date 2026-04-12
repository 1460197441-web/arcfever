const { invokeMockService } = require('./mock-data');

const NOW = '2026-03-19 10:00';

function buildPosts() {
  return [
    {
      id: 'post-001',
      title: '海洋观测仪器跨校共享的排期经验',
      tag: '仪器共享',
      author: '司艳文',
      excerpt: '从认证、预约到数据交付，把跨校共享里最容易踩坑的节点梳理成了标准流程。',
      content:
        '我们在青岛和烟台两地做了三轮联合测试，最后发现真正影响效率的不是设备本身，而是排期、交接记录和数据包标准。建议平台在下单前同步实验目的、样本量和交付格式。',
      likes: 36,
      comments: 12,
      createdAt: NOW
    },
    {
      id: 'post-002',
      title: '高精仪器租赁里，为什么保险和校准记录必须前置',
      tag: '风控讨论',
      author: '王海宁',
      excerpt: '高精度设备的争议，常常不在损坏，而在参数漂移和责任归属。',
      content:
        '对于高精仪器，平台应要求发布方在上架时提交最近一次校准时间、误差范围和损坏责任说明。买方下单前也应确认是否接受保险方案与赔付边界。',
      likes: 28,
      comments: 9,
      createdAt: NOW
    },
    {
      id: 'post-003',
      title: '远程实验不是视频演示，而是可验收的数据服务',
      tag: '远程实验',
      author: '杜星 教授团队',
      excerpt: '远程实验的核心不是“看见”，而是“交付可用数据”。',
      content:
        '我们建议远程实验服务统一沉淀为实验方案、原始数据、处理脚本、结果说明四件套，这样平台上的交易才真正可复用、可评价、可追责。',
      likes: 44,
      comments: 17,
      createdAt: NOW
    }
  ];
}

function buildProjects() {
  return [
    {
      id: 'proj-001',
      title: '海岸带风暴潮实验平台联合验证',
      owner: '青岛某海洋科技企业',
      company: '青岛某海洋科技企业',
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
      matches: [
        {
          name: '杜星 教授团队',
          title: '中国海洋大学 / 一海所',
          score: 96,
          tags: ['海洋灾害', '远程实验', '附带代码']
        },
        {
          name: '王海宁 博士后',
          title: '中国石油大学（华东）',
          score: 89,
          tags: ['岩芯分析', '图像识别']
        }
      ],
      flow: ['提交需求', '平台初筛', '候选团队匹配', '沟通排期', '签署协议并执行'],
      matrix: [
        { label: '设备匹配度', value: '94%' },
        { label: '交付稳定性', value: '88%' },
        { label: '协作效率', value: '91%' }
      ],
      needs: '联合完成风暴潮实验验证与分析报告。',
      createdAt: NOW
    },
    {
      id: 'proj-002',
      title: '生物材料表征共享测试计划',
      owner: '山东大学材料学院',
      company: '山东大学材料学院',
      domain: '生物材料',
      status: '评估中',
      intro: '围绕生物材料显微表征与数据处理，寻找长期合作测试资源。',
      budget: '3万 - 6万',
      duration: '4 周',
      keywords: ['生物材料', '显微表征', '共享测试'],
      targetRoles: ['科研工作者', '仪器供应方'],
      evaluation: {
        hard: '优先考察仪器精度、维护记录和历史服务案例。',
        soft: '关注响应速度、报告规范性和复测协作。'
      },
      matches: [
        {
          name: '刘海洋',
          title: '仪器供应方 / LabLink',
          score: 87,
          tags: ['驻场支持', '长期合作']
        }
      ],
      flow: ['发布需求', '资源匹配', '报价确认', '测试执行', '结果复盘'],
      matrix: [
        { label: '精度能力', value: '90%' },
        { label: '响应速度', value: '86%' },
        { label: '复用价值', value: '84%' }
      ],
      needs: '寻找共享测试设备与长期数据服务。',
      createdAt: NOW
    }
  ];
}

function buildSeedData() {
  const categories = invokeMockService('getCategories');
  const instrumentList = invokeMockService('getInstruments', { category: '全部', keyword: '' }).list;
  const profile = invokeMockService('getProfile');
  const agreement = invokeMockService('getAgreementContent');
  const schools = invokeMockService('getSchoolList').list;
  const certificationList = invokeMockService('getCertificationList').list;
  const chatList = invokeMockService('getChatList').list;
  const chatDetail = invokeMockService('getChatDetail', { id: chatList[0] && chatList[0].id });
  const reportList = invokeMockService('getReportList').list;
  const disputeList = invokeMockService('getDisputeList').list;
  const ratingList = invokeMockService('getRatingList').list;

  const seedUserId = 'seed-user-001';
  const firstInstrument = instrumentList[0];
  const secondInstrument = instrumentList[1] || instrumentList[0];

  const demoOrders = [
    {
      id: 'ord-demo-001',
      instrumentId: firstInstrument.id,
      buyerUserId: seedUserId,
      buyerName: profile.certification.name,
      sellerId: firstInstrument.sellerId,
      sellerName: firstInstrument.sellerName,
      tradeMode: '租赁',
      startDate: '2026-03-15',
      endDate: '2026-03-17',
      rentDays: 3,
      dailyPrice: firstInstrument.price,
      salePrice: 0,
      rentalAmount: firstInstrument.price * 3,
      saleAmount: 0,
      insurancePlan: firstInstrument.insurancePlans[0],
      insuranceAccepted: true,
      insuranceFee: firstInstrument.insurancePlans[0].fee * 3,
      deposit: firstInstrument.deposit,
      platformServiceFee: firstInstrument.platformServiceFee,
      total:
        firstInstrument.price * 3 +
        firstInstrument.insurancePlans[0].fee * 3 +
        firstInstrument.deposit +
        firstInstrument.platformServiceFee,
      amount:
        firstInstrument.price * 3 +
        firstInstrument.insurancePlans[0].fee * 3 +
        firstInstrument.deposit +
        firstInstrument.platformServiceFee,
      remark: '用于论文模型验证',
      agreementAccepted: true,
      damageAccepted: true,
      status: '已完成',
      createdAt: '2026-03-15 09:20',
      agreementTitle: agreement.title,
      disputeEligible: true,
      deliveryType: firstInstrument.remote ? '远程实验排期' : '线下交接'
    },
    {
      id: 'ord-legacy-001',
      instrumentId: secondInstrument.id,
      buyerUserId: seedUserId,
      buyerName: profile.certification.name,
      sellerId: secondInstrument.sellerId,
      sellerName: secondInstrument.sellerName,
      tradeMode: '租赁',
      startDate: '2026-03-11',
      endDate: '2026-03-12',
      rentDays: 2,
      dailyPrice: secondInstrument.price,
      salePrice: 0,
      rentalAmount: secondInstrument.price * 2,
      saleAmount: 0,
      insurancePlan: secondInstrument.insurancePlans[0],
      insuranceAccepted: true,
      insuranceFee: secondInstrument.insurancePlans[0].fee * 2,
      deposit: secondInstrument.deposit,
      platformServiceFee: secondInstrument.platformServiceFee,
      total:
        secondInstrument.price * 2 +
        secondInstrument.insurancePlans[0].fee * 2 +
        secondInstrument.deposit +
        secondInstrument.platformServiceFee,
      amount:
        secondInstrument.price * 2 +
        secondInstrument.insurancePlans[0].fee * 2 +
        secondInstrument.deposit +
        secondInstrument.platformServiceFee,
      remark: '历史争议订单',
      agreementAccepted: true,
      damageAccepted: true,
      status: '争议处理中',
      createdAt: '2026-03-11 15:40',
      agreementTitle: agreement.title,
      disputeEligible: true,
      deliveryType: secondInstrument.remote ? '远程实验排期' : '线下交接'
    }
  ];

  return {
    users: [
      {
        _id: seedUserId,
        openid: 'mock-openid-001',
        name: profile.certification.name,
        role: profile.certification.role,
        avatarClass: 'a1',
        phone: profile.certification.phone,
        email: profile.certification.email,
        instituteId: profile.certification.instituteId,
        school: profile.certification.school,
        college: profile.certification.college,
        proofName: profile.certification.proofName,
        status: profile.certification.status,
        createdAt: NOW,
        updatedAt: NOW
      }
    ],
    schools: schools.map((item) => ({
      ...item,
      createdAt: NOW
    })),
    instruments: instrumentList.map((item) => ({
      ...item,
      createdAt: NOW,
      updatedAt: NOW
    })),
    agreements: [
      {
        ...agreement,
        isActive: true,
        createdAt: NOW
      }
    ],
    certifications: certificationList.map((item) => ({
      ...item,
      userId: seedUserId,
      createdAt: item.submittedAt
    })),
    categories: categories.categories.map((name, index) => ({
      id: `cat-${index + 1}`,
      name,
      createdAt: NOW
    })),
    favorites: [
      {
        id: 'fav-001',
        userId: seedUserId,
        instrumentId: firstInstrument.id,
        createdAt: NOW
      }
    ],
    cartItems: [],
    orders: demoOrders,
    chats: [
      {
        id: chatDetail.chat.id,
        instrumentId: chatDetail.chat.instrumentId,
        buyerUserId: seedUserId,
        sellerId: firstInstrument.sellerId,
        sellerName: chatDetail.chat.sellerName,
        sellerRole: chatDetail.chat.sellerRole,
        instrumentName: chatDetail.chat.instrumentName,
        supportIntervened: chatDetail.chat.supportIntervened,
        updatedAt: '10:26',
        createdAt: NOW
      }
    ],
    chatMessages: chatDetail.messages.map((item, index) => ({
      id: `chat-msg-${index + 1}`,
      chatId: chatDetail.chat.id,
      from: item.from,
      text: item.text,
      time: item.time,
      createdAt: NOW
    })),
    ratings: ratingList.map((item) => ({
      ...item,
      userId: seedUserId,
      createdAt: NOW
    })),
    reports: reportList.map((item) => ({
      ...item,
      reporterUserId: seedUserId,
      createdAt: NOW
    })),
    disputes: disputeList.map((item) => ({
      ...item,
      buyerUserId: seedUserId,
      createdAt: NOW
    })),
    posts: buildPosts(),
    projects: buildProjects(),
    aiTasks: []
  };
}

module.exports = {
  buildSeedData
};
