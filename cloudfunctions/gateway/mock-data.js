const APP_NAME = '\u795e\u7ecf\u7a81\u89e6';

const AGREEMENT = {
  id: 'agreement-001',
  version: 'v1.2',
  title: '\u79d1\u7814\u4eea\u5668\u79df\u8d41\u4e0e\u6570\u636e\u4ea4\u4ed8\u534f\u8bae',
  summary:
    '\u8986\u76d6\u79df\u8d41\u5468\u671f\u3001\u62bc\u91d1\u8981\u6c42\u3001\u8fdd\u7ea6\u89c4\u5219\u3001\u8bbe\u5907\u635f\u574f\u8d23\u4efb\u4ee5\u53ca\u6570\u636e/\u4ee3\u7801\u4ea4\u4ed8\u8bf4\u660e\u3002',
  items: [
    '\u79df\u8d41\u524d\u9700\u5b8c\u6210\u5b9e\u540d\u8ba4\u8bc1\u3001\u5b66\u6821/\u673a\u6784\u4fe1\u606f\u6821\u9a8c\u4e0e\u534f\u8bae\u52fe\u9009\u3002',
    '\u62bc\u91d1\u5728\u8bbe\u5907\u6309\u671f\u5f52\u8fd8\u5e76\u7ecf\u5356\u5bb6\u786e\u8ba4\u540e\u539f\u8def\u9000\u56de\u3002',
    '\u9009\u8d2d\u8bbe\u5907\u4fdd\u9669\u540e\uff0c\u7b26\u5408\u4fdd\u969c\u6761\u4ef6\u7684\u7ef4\u4fee\u6216\u8fd0\u8f93\u635f\u8017\u53ef\u7531\u4fdd\u9669\u9879\u5206\u62c5\u3002',
    '\u82e5\u53d1\u751f\u8fdd\u7ea6\u3001\u8bbe\u5907\u635f\u574f\u6216\u4ea4\u4ed8\u4e89\u8bae\uff0c\u5e73\u53f0\u53ef\u57fa\u4e8e\u804a\u5929\u8bb0\u5f55\u3001\u68c0\u9a8c\u8bb0\u5f55\u548c\u534f\u8bae\u6761\u6b3e\u4ecb\u5165\u534f\u8c03\u3002'
  ]
};

const INSURANCE_PLANS = [
  {
    id: 'ins-plan-basic',
    name: '\u57fa\u7840\u8bbe\u5907\u9669',
    fee: 28,
    coverage: '\u6700\u9ad8\u8d54\u4ed8 5000 \u5143',
    desc: '\u9002\u5408\u5e38\u89c4\u79df\u8d41\uff0c\u6db5\u76d6\u8fd0\u8f93\u78d5\u78b0\u4e0e\u4e00\u822c\u90e8\u4ef6\u635f\u8017\u3002'
  },
  {
    id: 'ins-plan-pro',
    name: '\u9ad8\u7cbe\u4eea\u5668\u9669',
    fee: 66,
    coverage: '\u6700\u9ad8\u8d54\u4ed8 20000 \u5143',
    desc: '\u9762\u5411\u9ad8\u7cbe\u5ea6\u4eea\u5668\u6216\u8fdc\u7a0b\u5b9e\u9a8c\u573a\u666f\uff0c\u652f\u6301\u53c2\u6570\u6f02\u79fb\u4e0e\u6821\u51c6\u635f\u5931\u7406\u8d54\u3002'
  }
];

const VERIFIED_SCHOOLS = [
  {
    id: 'sch-001',
    name: '\u4e2d\u56fd\u6d77\u6d0b\u5927\u5b66',
    colleges: [
      '\u6d77\u6d0b\u5730\u7403\u79d1\u5b66\u5b66\u9662',
      '\u6d77\u6d0b\u4e0e\u5927\u6c14\u5b66\u9662',
      '\u4fe1\u606f\u79d1\u5b66\u4e0e\u5de5\u7a0b\u5b66\u90e8'
    ]
  },
  {
    id: 'sch-002',
    name: '\u4e2d\u56fd\u77f3\u6cb9\u5927\u5b66\uff08\u534e\u4e1c\uff09',
    colleges: [
      '\u5730\u7403\u79d1\u5b66\u4e0e\u6280\u672f\u5b66\u9662',
      '\u673a\u7535\u5de5\u7a0b\u5b66\u9662',
      '\u63a7\u5236\u79d1\u5b66\u4e0e\u5de5\u7a0b\u5b66\u9662'
    ]
  },
  {
    id: 'sch-003',
    name: '\u5c71\u4e1c\u5927\u5b66',
    colleges: [
      '\u73af\u5883\u79d1\u5b66\u4e0e\u5de5\u7a0b\u5b66\u9662',
      '\u6d77\u6d0b\u5b66\u9662',
      '\u6750\u6599\u79d1\u5b66\u4e0e\u5de5\u7a0b\u5b66\u9662'
    ]
  }
];

const CATEGORIES = [
  '\u5168\u90e8',
  '\u6d77\u6d0b\u89c2\u6d4b',
  '\u5730\u8d28\u707e\u5bb3',
  '\u751f\u7269\u6750\u6599',
  '\u5316\u5b66\u5206\u6790',
  '\u9ad8\u7cbe\u4eea\u5668'
];

function makeDateRange(startDay, count) {
  const baseDate = new Date(2026, 2, startDay);
  return Array.from({ length: count }, (_, idx) => {
    const current = new Date(baseDate);
    current.setDate(baseDate.getDate() + idx);
    const year = current.getFullYear();
    const month = String(current.getMonth() + 1).padStart(2, '0');
    const day = String(current.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  });
}

const state = {
  me: {
    id: 'u-001',
    name: '\u53f8\u8273\u6587',
    role: '\u79d1\u7814\u5de5\u4f5c\u8005',
    avatarClass: 'a1',
    phone: '13800138000',
    email: 'siyanwen@ouc.edu.cn',
    instituteId: '20260001',
    school: '\u4e2d\u56fd\u6d77\u6d0b\u5927\u5b66',
    college: '\u6d77\u6d0b\u5730\u7403\u79d1\u5b66\u5b66\u9662',
    proofName: 'ouc-lab-proof.pdf',
    status: '\u5df2\u8ba4\u8bc1'
  },
  certificationApplications: [
    {
      id: 'cert-001',
      name: '\u53f8\u8273\u6587',
      role: '\u79d1\u7814\u5de5\u4f5c\u8005',
      phone: '13800138000',
      email: 'siyanwen@ouc.edu.cn',
      instituteId: '20260001',
      school: '\u4e2d\u56fd\u6d77\u6d0b\u5927\u5b66',
      college: '\u6d77\u6d0b\u5730\u7403\u79d1\u5b66\u5b66\u9662',
      proofName: 'ouc-lab-proof.pdf',
      status: '\u5df2\u901a\u8fc7',
      submittedAt: '2026-03-17 10:15'
    },
    {
      id: 'cert-002',
      name: '\u5218\u6d77\u6d0b',
      role: '\u4eea\u5668\u4f9b\u5e94\u65b9',
      phone: '13988887777',
      email: 'sales@lablink.cn',
      instituteId: 'SUP-3102',
      school: '\u5c71\u4e1c\u5927\u5b66',
      college: '\u6750\u6599\u79d1\u5b66\u4e0e\u5de5\u7a0b\u5b66\u9662',
      proofName: 'supplier-license.pdf',
      status: '\u5f85\u5ba1\u6838',
      submittedAt: '2026-03-19 11:05'
    }
  ],
  instruments: [
    {
      id: 'ins-001',
      name: '\u6ce2\u6d6a\u4f5c\u7528\u4e0b\u6c89\u79ef\u7269\u5b54\u538b\u54cd\u5e94\u6a21\u62df\u88c5\u7f6e',
      category: '\u6d77\u6d0b\u89c2\u6d4b',
      sellerId: 'u-101',
      sellerName: '\u675c\u661f \u6559\u6388\u56e2\u961f',
      sellerRole: '\u9ad8\u6821\u6559\u5e08',
    institute: '\u4e2d\u56fd\u6d77\u6d0b\u5927\u5b66 / \u4e00\u6d77\u6240',
    school: '\u4e2d\u56fd\u6d77\u6d0b\u5927\u5b66',
    college: '\u6d77\u6d0b\u5730\u7403\u79d1\u5b66\u5b66\u9662',
    verifiedType: 'blue',
      avatarClass: 'a1',
      posterTheme: 'poster-theme-1',
      location: '\u9752\u5c9b\u5e02 \u00b7 \u5d02\u5c71\u533a',
      phone: '13800138011',
      email: 'duxing@ouc.edu.cn',
    price: 300,
    priceLabel: '\u00a5300 / \u5929',
    salePrice: 6800,
    salePriceLabel: '\u00a56800 \u4e70\u65ad',
    tradeModes: ['\u79df\u8d41', '\u51fa\u552e'],
    defaultTradeMode: '\u79df\u8d41',
    deposit: 1200,
      platformServiceFee: 24,
      desc:
        '\u53ef\u9ad8\u7cbe\u5ea6\u9884\u6d4b\u6ce2\u6d6a\u5f15\u8d77\u7684\u5b54\u9699\u6c34\u538b\u529b\uff0c\u9002\u7528\u4e8e\u6d77\u6d0b\u707e\u5bb3\u6a21\u62df\u4e0e\u5730\u8d28\u65f6\u95f4\u5e8f\u5217\u5206\u6790\u3002',
      precision: '\u8bef\u5dee\u5c0f\u4e8e 2 kPa',
      disciplines: ['\u6d77\u6d0b\u707e\u5bb3', '\u6c89\u79ef\u52a8\u529b\u5b66', '\u5ca9\u571f\u5de5\u7a0b'],
      withDataPackage: true,
      remote: true,
      supportInsurance: true,
      availableDates: makeDateRange(20, 10),
      tags: ['\u8fdc\u7a0b\u5b9e\u9a8c', '\u9644\u5e26\u4ee3\u7801', '\u6559\u5e08\u56e2\u961f'],
      condition: '\u5b9e\u9a8c\u5ba4\u5728\u5f79',
      publishStatus: '\u5df2\u4e0a\u67b6',
      breachRules: [
        '\u8d85\u65f6\u5f52\u8fd8\u6bcf\u65e5\u6309\u65e5\u79df\u91d1 10% \u8ba1\u6536\u8fdd\u7ea6\u91d1',
        '\u65e0\u6545\u53d6\u6d88\u8ba2\u5355\u5c06\u6263\u9664\u5e73\u53f0\u670d\u52a1\u8d39',
        '\u672a\u7ecf\u6388\u6743\u64c5\u81ea\u62c6\u5378\u4f7f\u7528\u5c06\u89e6\u53d1\u4fdd\u8bc1\u91d1\u6263\u51cf'
      ],
      damageRules: [
        '\u4eba\u4e3a\u635f\u574f\u6309\u7ef4\u4fee\u62a5\u4ef7\u6216\u4f30\u503c\u8d54\u4ed8',
        '\u53d1\u751f\u7cbe\u5ea6\u6f02\u79fb\u65f6\u9700\u627f\u62c5\u6821\u51c6\u6210\u672c',
        '\u7269\u6d41\u8fd0\u8f93\u635f\u574f\u4f18\u5148\u6309\u4fdd\u9669\u7406\u8d54\u89c4\u5219\u5904\u7406'
      ],
      insurancePlans: INSURANCE_PLANS,
      agreementId: AGREEMENT.id,
      servicePackage: '\u9644\u5e26\u6807\u51c6\u6570\u636e\u96c6\u4e0e\u5904\u7406\u4ee3\u7801'
    }
  ],
  cartItems: [],
  favorites: ['ins-001'],
  orders: [],
  messages: {
    'chat-001': {
      id: 'chat-001',
      instrumentId: 'ins-001',
      sellerName: '\u675c\u661f \u6559\u6388\u56e2\u961f',
      sellerRole: '\u9ad8\u6821\u6559\u5e08',
      instrumentName: '\u6ce2\u6d6a\u4f5c\u7528\u4e0b\u6c89\u79ef\u7269\u5b54\u538b\u54cd\u5e94\u6a21\u62df\u88c5\u7f6e',
      updatedAt: '10:26',
      supportIntervened: false,
      messages: [
        {
          from: 'seller',
          text: '\u4f60\u597d\uff0c\u8fd9\u53f0\u88c5\u7f6e\u76ee\u524d\u53ef\u79df\uff0c\u652f\u6301\u8fdc\u7a0b\u5b9e\u9a8c\u534f\u52a9\u3002',
          time: '10:12'
        },
        {
          from: 'buyer',
          text: '\u6211\u662f\u6d77\u6d0b\u707e\u5bb3\u65b9\u5411\u7684\u535a\u58eb\u751f\uff0c\u60f3\u79df 3 \u5929\uff0c\u662f\u5426\u80fd\u9644\u6807\u51c6\u6570\u636e\u5305\uff1f',
          time: '10:18'
        },
        {
          from: 'seller',
          text: '\u53ef\u4ee5\uff0c\u4f1a\u9644\u5e26\u57fa\u7840\u6570\u636e\u96c6\u548c Python \u5904\u7406\u811a\u672c\u3002',
          time: '10:26'
        }
      ]
    }
  },
  ratings: [
    {
      id: 'rate-001',
      orderId: 'ord-demo-001',
      target: '\u6ce2\u6d6a\u4f5c\u7528\u4e0b\u6c89\u79ef\u7269\u5b54\u538b\u54cd\u5e94\u6a21\u62df\u88c5\u7f6e',
      score: 5,
      content: '\u6c9f\u901a\u4e13\u4e1a\uff0c\u6570\u636e\u5305\u5b8c\u6574\uff0c\u9002\u5408\u8bba\u6587\u6a21\u578b\u8fdb\u884c\u57fa\u7ebf\u9a8c\u8bc1\u3002'
    }
  ],
  reports: [
    {
      id: 'report-001',
      targetType: '\u4eea\u5668',
      targetName: '\u9ad8\u538b\u53cd\u5e94\u4ed3',
      reason: '\u53d1\u5e03\u4fe1\u606f\u4e0e\u771f\u5b9e\u7cbe\u5ea6\u4e0d\u4e00\u81f4',
      reporter: '\u5468\u5b81',
      status: '\u5f85\u5904\u7406'
    }
  ],
  disputes: [
    {
      id: 'dispute-001',
      orderId: 'ord-legacy-001',
      summary: '\u5356\u65b9\u4e3b\u5f20\u8bbe\u5907\u955c\u5934\u53d7\u635f\uff0c\u4e70\u65b9\u8ba4\u4e3a\u4ea4\u4ed8\u524d\u5373\u5b58\u5728\u65e7\u75d5',
      status: '\u5e73\u53f0\u8c03\u89e3\u4e2d',
      assignee: '\u5e73\u53f0\u5ba2\u670d 01'
    }
  ],
  pendingCertification: 1
};

function clone(data) {
  return JSON.parse(JSON.stringify(data));
}

function asPriceLabel(price) {
  return `\u00a5${price} / \u5929`;
}

function nowString() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day} ${hours}:${minutes}`;
}

function validatePhone(phone) {
  return /^1\d{10}$/.test(phone);
}

function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function getInstrumentById(id) {
  return state.instruments.find((item) => item.id === id);
}

function getInsurancePlanById(id) {
  return INSURANCE_PLANS.find((item) => item.id === id) || INSURANCE_PLANS[0];
}

function dayDiff(startDate, endDate) {
  const start = new Date(startDate);
  const end = new Date(endDate);
  const diff = Math.ceil((end - start) / (24 * 60 * 60 * 1000)) + 1;
  return diff > 0 ? diff : 1;
}

function ensureVerified(actionName) {
  if (state.me.status !== '\u5df2\u8ba4\u8bc1') {
    throw new Error(`${actionName || '\u5f53\u524d\u64cd\u4f5c'}\u4ec5\u5bf9\u5df2\u8ba4\u8bc1\u7528\u6237\u5f00\u653e`);
  }
}

function normalizeTradeModes(tradeModes, fallbackModes = ['\u79df\u8d41']) {
  const source = Array.isArray(tradeModes)
    ? tradeModes
    : String(tradeModes || '')
        .split(/[\u3001\uff0c,/\s]+/)
        .filter(Boolean);
  const modes = source.filter(
    (mode, index, list) =>
      ['\u79df\u8d41', '\u51fa\u552e'].includes(mode) && list.indexOf(mode) === index
  );
  return modes.length ? modes : clone(fallbackModes);
}

function normalizeTradeMode(instrument, tradeMode) {
  const modes = normalizeTradeModes(
    instrument.tradeModes,
    [instrument.defaultTradeMode || '\u79df\u8d41']
  );
  if (tradeMode && modes.includes(tradeMode)) return tradeMode;
  if (instrument.defaultTradeMode && modes.includes(instrument.defaultTradeMode)) {
    return instrument.defaultTradeMode;
  }
  return modes[0];
}

function normalizeDateSelection(instrument, startDate, endDate) {
  const dates = instrument.availableDates || [];
  const defaultStart = dates[0] || '2026-03-20';
  const start = startDate && dates.includes(startDate) ? startDate : defaultStart;
  let end = endDate && dates.includes(endDate) ? endDate : start;
  if (new Date(end) < new Date(start)) {
    end = start;
  }
  return {
    startDate: start,
    endDate: end
  };
}

function buildCartItem(item) {
  const instrument = getInstrumentById(item.instrumentId);
  if (!instrument) return null;
  const tradeMode = normalizeTradeMode(instrument, item.tradeMode);
  const insurancePlan = getInsurancePlanById(item.insurancePlanId || INSURANCE_PLANS[0].id);
  const quantity = item.quantity || 1;
  const insuranceAccepted = !!item.insuranceAccepted;
  const platformServiceFee = instrument.platformServiceFee;
  let startDate = '';
  let endDate = '';
  let rentDays = 0;
  let rentalAmount = 0;
  let saleAmount = 0;
  let deposit = 0;
  let insuranceFee = 0;
  let amountLabel = instrument.priceLabel;
  let dateLabel = '\u4e00\u6b21\u6027\u4ea4\u4ed8';

  if (tradeMode === '\u51fa\u552e') {
    saleAmount = instrument.salePrice || 0;
    insuranceFee = insuranceAccepted ? insurancePlan.fee * quantity : 0;
    amountLabel = instrument.salePriceLabel || `\u00a5${instrument.salePrice || 0} \u4e70\u65ad`;
  } else {
    const selection = normalizeDateSelection(instrument, item.startDate, item.endDate);
    startDate = selection.startDate;
    endDate = selection.endDate;
    rentDays = dayDiff(startDate, endDate);
    rentalAmount = instrument.price * rentDays * quantity;
    deposit = instrument.deposit;
    insuranceFee = insuranceAccepted ? insurancePlan.fee * rentDays * quantity : 0;
    amountLabel = instrument.priceLabel;
    dateLabel = `${startDate} ~ ${endDate}`;
  }

  const total = rentalAmount + saleAmount + insuranceFee + deposit + platformServiceFee;
  return {
    ...item,
    instrument,
    tradeMode,
    insurancePlan,
    insuranceAccepted,
    quantity,
    startDate,
    endDate,
    dateLabel,
    rentDays,
    rentalAmount,
    saleAmount,
    insuranceFee,
    deposit,
    platformServiceFee,
    total,
    amountLabel
  };
}

function summarizeCart(list) {
  return {
    total: list.reduce((sum, item) => sum + item.total, 0),
    depositTotal: list.reduce((sum, item) => sum + item.deposit, 0),
    insuranceTotal: list.reduce((sum, item) => sum + item.insuranceFee, 0),
    rentalTotal: list.reduce((sum, item) => sum + item.rentalAmount, 0),
    saleTotal: list.reduce((sum, item) => sum + item.saleAmount, 0),
    serviceTotal: list.reduce((sum, item) => sum + item.platformServiceFee, 0),
    itemCount: list.length
  };
}

function cartDetail() {
  const list = state.cartItems.map(buildCartItem).filter(Boolean);
  return {
    list: clone(list),
    ...summarizeCart(list)
  };
}

state.instruments.push(
  {
    id: 'ins-002',
    name: '\u5ca9\u82af\u8584\u7247\u667a\u80fd\u626b\u63cf\u4eea',
    category: '\u5730\u8d28\u707e\u5bb3',
    sellerId: 'u-202',
    sellerName: '\u738b\u6d77\u5b81 \u535a\u58eb\u540e',
    sellerRole: '\u79d1\u7814\u5de5\u4f5c\u8005',
    institute: '\u4e2d\u56fd\u77f3\u6cb9\u5927\u5b66\uff08\u534e\u4e1c\uff09',
    school: '\u4e2d\u56fd\u77f3\u6cb9\u5927\u5b66\uff08\u534e\u4e1c\uff09',
    college: '\u5730\u7403\u79d1\u5b66\u4e0e\u6280\u672f\u5b66\u9662',
    verifiedType: 'green',
    avatarClass: 'a2',
    posterTheme: 'poster-theme-2',
    location: '\u70df\u53f0\u5e02 \u00b7 \u9ad8\u65b0\u533a',
    phone: '13900139000',
    email: 'wanghn@upc.edu.cn',
    price: 260,
    priceLabel: '\u00a5260 / \u5929',
    salePrice: 4200,
    salePriceLabel: '\u00a54200 \u4e70\u65ad',
    tradeModes: ['\u79df\u8d41'],
    defaultTradeMode: '\u79df\u8d41',
    deposit: 900,
    platformServiceFee: 18,
    desc:
      '\u9002\u7528\u4e8e\u5ca9\u82af\u88c2\u9699\u3001\u77ff\u7269\u5206\u5e03\u4e0e\u6ed1\u5761\u6750\u6599\u8bc6\u522b\uff0c\u652f\u6301 AI \u8f85\u52a9\u9884\u6807\u6ce8\u3002',
    precision: '2400 dpi \u626b\u63cf\u7cbe\u5ea6',
    disciplines: ['\u5ca9\u77f3\u529b\u5b66', '\u5730\u8d28\u707e\u5bb3', '\u56fe\u50cf\u5206\u6790'],
    withDataPackage: true,
    remote: false,
    supportInsurance: true,
    availableDates: makeDateRange(22, 8),
    tags: ['\u6837\u54c1\u626b\u63cf', '\u652f\u6301\u4e0a\u95e8\u770b\u673a'],
    condition: '\u6821\u51c6\u5b8c\u6210',
    publishStatus: '\u5df2\u4e0a\u67b6',
    breachRules: [
      '\u8d85\u65f6\u5f52\u8fd8\u6309\u65e5\u79df\u91d1 15% \u7d2f\u79ef',
      '\u6837\u54c1\u63cf\u8ff0\u4e0d\u5b9e\u9020\u6210\u6362\u673a\uff0c\u4e70\u65b9\u9700\u627f\u62c5\u57fa\u7840\u670d\u52a1\u8d39'
    ],
    damageRules: [
      '\u955c\u5934\u3001\u626b\u63cf\u5e73\u53f0\u6216\u5b9a\u4f4d\u6a21\u5757\u635f\u574f\u9700\u6309\u7ef4\u4fee\u6e05\u5355\u8d54\u4ed8',
      '\u5f3a\u5236\u65ad\u7535\u5bfc\u81f4\u6570\u636e\u635f\u574f\u4e0d\u5728\u9000\u8d39\u8303\u56f4'
    ],
    insurancePlans: INSURANCE_PLANS,
    agreementId: AGREEMENT.id,
    servicePackage: '\u53ef\u9009\u57fa\u7840\u56fe\u50cf\u6570\u636e\u5305'
  },
  {
    id: 'ins-003',
    name: '\u591a\u529f\u80fd\u751f\u7269\u6750\u6599\u529b\u5b66\u6d4b\u8bd5\u53f0',
    category: '\u751f\u7269\u6750\u6599',
    sellerId: 'u-303',
    sellerName: '\u8054\u79d1\u4eea\u5668\u4f9b\u5e94\u4e2d\u5fc3',
    sellerRole: '\u4eea\u5668\u4f9b\u5e94\u65b9',
    institute: '\u8054\u79d1\u5b9e\u9a8c\u88c5\u5907\u516c\u53f8',
    school: '\u5c71\u4e1c\u5927\u5b66',
    college: '\u6750\u6599\u79d1\u5b66\u4e0e\u5de5\u7a0b\u5b66\u9662',
    verifiedType: 'blue',
    avatarClass: 'a3',
    posterTheme: 'poster-theme-3',
    location: '\u4e0a\u6d77\u5e02 \u00b7 \u6d66\u4e1c\u65b0\u533a',
    phone: '13733334444',
    email: 'service@lablink.cn',
    price: 450,
    priceLabel: '\u00a5450 / \u5929',
    salePrice: 9200,
    salePriceLabel: '\u00a59200 \u4e70\u65ad',
    tradeModes: ['\u79df\u8d41', '\u51fa\u552e'],
    defaultTradeMode: '\u79df\u8d41',
    deposit: 1800,
    platformServiceFee: 30,
    desc:
      '\u9002\u7528\u4e8e\u751f\u7269\u533b\u7528\u6750\u6599\u3001\u9ad8\u5206\u5b50\u819c\u6750\u6599\u548c\u590d\u5408\u6750\u6599\u7684\u62c9\u4f38\u4e0e\u538b\u7f29\u529b\u5b66\u5206\u6790\u3002',
    precision: '\u4f4d\u79fb\u5206\u8fa8\u7387 0.01 mm',
    disciplines: ['\u751f\u7269\u6750\u6599', '\u9ad8\u5206\u5b50\u5de5\u7a0b', '\u533b\u5de5\u7ed3\u5408'],
    withDataPackage: false,
    remote: true,
    supportInsurance: true,
    availableDates: makeDateRange(21, 12),
    tags: ['\u4f9b\u5e94\u5546', '\u652f\u6301\u8fdc\u7a0b\u503c\u5b88', '\u53ef\u9001\u8d27\u4e0a\u95e8'],
    condition: '\u65b0\u673a',
    publishStatus: '\u5df2\u4e0a\u67b6',
    breachRules: [
      '\u9ad8\u4ef7\u4eea\u5668\u9700\u5148\u652f\u4ed8\u62bc\u91d1\u624d\u53ef\u9501\u5b9a\u6392\u671f',
      '\u53d6\u6d88\u79df\u8d41\u8ddd\u542f\u52a8 24 \u5c0f\u65f6\u5185\uff0c\u5e73\u53f0\u670d\u52a1\u8d39\u4e0d\u9000'
    ],
    damageRules: [
      '\u4eba\u4e3a\u8d85\u8f7d\u9020\u6210\u7684\u4f20\u611f\u5668\u635f\u574f\u7531\u79df\u7528\u65b9\u627f\u62c5',
      '\u4ea4\u63a5\u5f53\u65e5\u5982\u53d1\u73b0\u5916\u89c2\u5f02\u5e38\u9700 2 \u5c0f\u65f6\u5185\u53cd\u9988'
    ],
    insurancePlans: INSURANCE_PLANS,
    agreementId: AGREEMENT.id,
    servicePackage: '\u53ef\u52a0\u8d2d\u6807\u51c6\u6d4b\u8bd5\u62a5\u544a'
  }
);

function homeData() {
  return {
    hero: {
      title: '\u795e\u7ecf\u7a81\u89e6\u4eea\u5668\u79df\u8d41\u4e0e\u5b66\u672f\u4ea4\u6d41',
      subtitle:
        '\u4ee5\u9ad8\u6821\u8ba4\u8bc1\u3001\u79d1\u7814\u80cc\u4e66\u548c\u4eea\u5668\u98ce\u63a7\u4e3a\u6838\u5fc3\uff0c\u628a\u79df\u8d41\u3001\u6570\u636e\u4ea4\u4ed8\u3001\u8fdc\u7a0b\u5b9e\u9a8c\u548c\u5b66\u672f\u6c9f\u901a\u505a\u6210\u4e00\u6761\u771f\u5b9e\u94fe\u8def\u3002'
    },
    featuredInstruments: clone(state.instruments),
    stats: [
      { label: '\u8ba4\u8bc1\u9662\u6821', value: `${VERIFIED_SCHOOLS.length} \u6240` },
      { label: '\u5728\u67b6\u4eea\u5668', value: `${state.instruments.length} \u53f0` },
      { label: '\u5f85\u5ba1\u6838\u8ba4\u8bc1', value: `${state.pendingCertification} \u6761` }
    ]
  };
}

function schoolOptions() {
  return clone(VERIFIED_SCHOOLS);
}

function certificationOverview() {
  const statusMessageMap = {
    '\u5df2\u8ba4\u8bc1':
      '\u4f60\u7684\u79d1\u7814\u8eab\u4efd\u5df2\u7ecf\u901a\u8fc7\u5e73\u53f0\u8ba4\u8bc1\uff0c\u53ef\u4ee5\u53d1\u5e03\u4eea\u5668\u3001\u53d1\u8d77\u79df\u8d41/\u4e70\u65ad\u4ea4\u6613\uff0c\u5e76\u4f7f\u7528\u5e73\u53f0\u98ce\u63a7\u4e0e\u5ba2\u670d\u4ecb\u5165\u670d\u52a1\u3002',
    '\u5f85\u5ba1\u6838':
      '\u4f60\u7684\u8ba4\u8bc1\u4fe1\u606f\u5df2\u8fdb\u5165\u5ba1\u6838\u6d41\u7a0b\uff0c\u5ba1\u6838\u901a\u8fc7\u540e\u5c06\u89e3\u9501\u5b8c\u6574\u4ea4\u6613\u80fd\u529b\u4e0e\u5e73\u53f0\u627f\u4fdd\u670d\u52a1\u3002'
  };
  return {
    status: state.me.status,
    name: state.me.name,
    role: state.me.role,
    phone: state.me.phone,
    email: state.me.email,
    instituteId: state.me.instituteId,
    school: state.me.school,
    college: state.me.college,
    proofName: state.me.proofName,
    pendingMessage:
      statusMessageMap[state.me.status] ||
      '\u5efa\u8bae\u5b8c\u5584\u8ba4\u8bc1\u8d44\u6599\uff0c\u4ee5\u786e\u4fdd\u4ea4\u6613\u5bf9\u8c61\u3001\u673a\u6784\u4fe1\u606f\u4e0e\u4ea4\u4ed8\u8d23\u4efb\u5168\u90e8\u53ef\u8ffd\u6eaf\u3002'
  };
}

function getChatList() {
  return Object.values(state.messages).map((item) => ({
    id: item.id,
    sellerName: item.sellerName,
    sellerRole: item.sellerRole,
    instrumentName: item.instrumentName,
    lastMessage: item.messages[item.messages.length - 1].text,
    updatedAt: item.updatedAt,
    supportIntervened: item.supportIntervened
  }));
}

function invokeMockService(action, payload = {}) {
  switch (action) {
    case 'getHomeData':
      return homeData();
    case 'getCategories':
      return { categories: clone(CATEGORIES), schools: schoolOptions() };
    case 'getInstruments': {
      const keyword = (payload.keyword || '').trim();
      const category = payload.category || '\u5168\u90e8';
      const list = state.instruments.filter((item) => {
        const categoryMatched = category === '\u5168\u90e8' || item.category === category;
        const keywordMatched =
          !keyword ||
          item.name.includes(keyword) ||
          item.institute.includes(keyword) ||
          item.disciplines.some((subject) => subject.includes(keyword)) ||
          item.tags.some((tag) => tag.includes(keyword));
        return categoryMatched && keywordMatched;
      });
      return { categories: clone(CATEGORIES), list: clone(list) };
    }
    case 'getInstrumentDetail': {
      const instrument = getInstrumentById(payload.id) || state.instruments[0];
      return {
        instrument: clone(instrument),
        isFavorite: state.favorites.includes(instrument.id),
        recommendations: clone(state.instruments.filter((item) => item.id !== instrument.id).slice(0, 2)),
        agreement: clone(AGREEMENT)
      };
    }
    case 'toggleFavorite': {
      const idx = state.favorites.indexOf(payload.instrumentId);
      if (idx >= 0) state.favorites.splice(idx, 1);
      else state.favorites.unshift(payload.instrumentId);
      const isFavorite = state.favorites.includes(payload.instrumentId);
      return {
        success: true,
        isFavorite,
        message: isFavorite ? '\u5df2\u52a0\u5165\u6536\u85cf' : '\u5df2\u53d6\u6d88\u6536\u85cf'
      };
    }
    case 'addToCart': {
      ensureVerified('\u52a0\u5165\u8d2d\u7269\u8f66');
      const instrument = getInstrumentById(payload.instrumentId);
      if (!instrument) throw new Error('\u672a\u627e\u5230\u4eea\u5668');
      const tradeMode = normalizeTradeMode(instrument, payload.tradeMode);
      const dateSelection = normalizeDateSelection(
        instrument,
        payload.startDate,
        payload.endDate
      );
      const insurancePlanId = payload.insurancePlanId || instrument.insurancePlans[0].id;
      const insuranceAccepted = !!payload.insuranceAccepted;
      const existing = state.cartItems.find(
        (item) =>
          item.instrumentId === instrument.id &&
          normalizeTradeMode(instrument, item.tradeMode) === tradeMode
      );
      if (existing) {
        existing.tradeMode = tradeMode;
        existing.startDate = dateSelection.startDate;
        existing.endDate = dateSelection.endDate;
        existing.insurancePlanId = insurancePlanId;
        existing.insuranceAccepted = insuranceAccepted;
      } else {
        state.cartItems.unshift({
          id: `cart-${Date.now()}`,
          instrumentId: instrument.id,
          tradeMode,
          startDate: dateSelection.startDate,
          endDate: dateSelection.endDate,
          insurancePlanId,
          insuranceAccepted,
          quantity: 1
        });
      }
      return {
        success: true,
        message: '\u5df2\u52a0\u5165\u8d2d\u7269\u8f66',
        cartCount: state.cartItems.length
      };
    }
    case 'removeCartItem':
      state.cartItems = state.cartItems.filter((item) => item.id !== payload.id);
      return { success: true };
    case 'getCart':
      return cartDetail();
    case 'getOrderPreview': {
      let detail = cartDetail();
      let first = detail.list[0];

      if (payload.instrumentId) {
        const targetInstrument = getInstrumentById(payload.instrumentId);
        if (!targetInstrument) throw new Error('\u672a\u627e\u5230\u4eea\u5668');
        const existing =
          state.cartItems.find((item) => item.instrumentId === targetInstrument.id) || {};
        const previewItem = buildCartItem({
          id: existing.id || `preview-${targetInstrument.id}`,
          instrumentId: targetInstrument.id,
          tradeMode: payload.tradeMode || existing.tradeMode,
          startDate: payload.startDate || existing.startDate,
          endDate: payload.endDate || existing.endDate,
          insurancePlanId: payload.insurancePlanId || existing.insurancePlanId,
          insuranceAccepted:
            typeof payload.insuranceAccepted === 'boolean'
              ? payload.insuranceAccepted
              : !!existing.insuranceAccepted,
          quantity: 1
        });
        const list = previewItem ? [previewItem] : [];
        detail = {
          list: clone(list),
          ...summarizeCart(list)
        };
        first = previewItem;
      }

      return {
        ...detail,
        contactName: state.me.name,
        contactPhone: state.me.phone,
        contactEmail: state.me.email,
        agreement: clone(AGREEMENT),
        defaultAgreementAccepted: false,
        defaultInsuranceAccepted: first ? !!first.insuranceAccepted : false,
        defaultDamageAccepted: false,
        selectedInstrument: first ? clone(first.instrument) : null,
        selectedItem: first ? clone(first) : null
      };
    }
    case 'createOrder': {
      ensureVerified('\u4e0b\u5355');
      if (!payload.agreementAccepted || !payload.damageAccepted) {
        throw new Error('\u8bf7\u5148\u540c\u610f\u534f\u8bae\u4e0e\u635f\u574f\u8d23\u4efb\u8bf4\u660e');
      }
      const instrument =
        getInstrumentById(payload.instrumentId) ||
        getInstrumentById(state.cartItems[0] && state.cartItems[0].instrumentId) ||
        state.instruments[0];
      const tradeMode = normalizeTradeMode(instrument, payload.tradeMode);
      const insurancePlan = getInsurancePlanById(payload.insurancePlanId || instrument.insurancePlans[0].id);
      const insuranceAccepted = !!payload.insuranceAccepted;
      let startDate = '';
      let endDate = '';
      let rentDays = 0;
      let rentalAmount = 0;
      let saleAmount = 0;
      let deposit = 0;

      if (tradeMode === '\u79df\u8d41') {
        if (!payload.startDate || !payload.endDate) {
          throw new Error('\u8bf7\u9009\u62e9\u79df\u8d41\u65e5\u671f');
        }
        const selection = normalizeDateSelection(instrument, payload.startDate, payload.endDate);
        startDate = selection.startDate;
        endDate = selection.endDate;
        rentDays = dayDiff(startDate, endDate);
        rentalAmount = instrument.price * rentDays;
        deposit = instrument.deposit;
      } else {
        saleAmount = instrument.salePrice || 0;
        if (!saleAmount) {
          throw new Error('\u8be5\u4eea\u5668\u6682\u4e0d\u652f\u6301\u4e70\u65ad');
        }
      }

      const insuranceFee =
        insuranceAccepted ? insurancePlan.fee * (tradeMode === '\u79df\u8d41' ? rentDays : 1) : 0;
      const total =
        rentalAmount + saleAmount + insuranceFee + deposit + instrument.platformServiceFee;
      const order = {
        id: `ord-${Date.now()}`,
        instrumentId: instrument.id,
        buyerName: state.me.name,
        sellerName: instrument.sellerName,
        tradeMode,
        startDate,
        endDate,
        rentDays,
        dailyPrice: instrument.price,
        salePrice: instrument.salePrice || 0,
        rentalAmount,
        saleAmount,
        insurancePlan,
        insuranceAccepted,
        insuranceFee,
        deposit,
        platformServiceFee: instrument.platformServiceFee,
        total,
        amount: total,
        remark: payload.remark || '',
        agreementAccepted: true,
        damageAccepted: true,
        status: '\u5f85\u4ed8\u6b3e',
        createdAt: nowString(),
        agreementTitle: AGREEMENT.title,
        disputeEligible: true,
        deliveryType:
          tradeMode === '\u51fa\u552e'
            ? '\u5e73\u53f0\u9a8c\u8d27\u4e0e\u7269\u6d41\u4ea4\u4ed8'
            : instrument.remote
              ? '\u8fdc\u7a0b\u5b9e\u9a8c\u6392\u671f'
              : '\u7ebf\u4e0b\u4ea4\u63a5'
      };
      state.orders.unshift(order);
      state.cartItems = state.cartItems.filter(
        (item) =>
          !(
            item.instrumentId === instrument.id &&
            normalizeTradeMode(instrument, item.tradeMode) === tradeMode
          )
      );
      return { success: true, orderId: order.id, amount: order.total };
    }
    case 'getPaymentInfo':
      return { order: clone(state.orders.find((item) => item.id === payload.orderId) || state.orders[0]) };
    case 'confirmPayment': {
      const order = state.orders.find((item) => item.id === payload.orderId);
      if (!order) throw new Error('\u672a\u627e\u5230\u8ba2\u5355');
      order.status =
        order.tradeMode === '\u51fa\u552e'
          ? '\u5df2\u4ed8\u6b3e\u5f85\u53d1\u8d27'
          : '\u5df2\u4ed8\u6b3e\u5f85\u6392\u671f';
      return { success: true, orderId: order.id };
    }
    case 'getChatList':
      return { list: clone(getChatList()) };
    case 'getChatDetail': {
      const chat = state.messages[payload.id] || Object.values(state.messages)[0];
      return {
        chat: clone({
          id: chat.id,
          instrumentId: chat.instrumentId,
          sellerName: chat.sellerName,
          sellerRole: chat.sellerRole,
          instrumentName: chat.instrumentName,
          supportIntervened: chat.supportIntervened
        }),
        messages: clone(chat.messages)
      };
    }
    case 'sendChatMessage': {
      const chat = state.messages[payload.chatId];
      if (!chat) throw new Error('\u4f1a\u8bdd\u4e0d\u5b58\u5728');
      if (!String(payload.text || '').trim()) throw new Error('\u8bf7\u8f93\u5165\u6d88\u606f\u5185\u5bb9');
      chat.messages.push({
        from: 'buyer',
        text: String(payload.text).trim(),
        time: nowString().slice(11, 16)
      });
      chat.updatedAt = nowString().slice(11, 16);
      return { success: true, messages: clone(chat.messages) };
    }
    case 'requestSupportIntervention': {
      const chat = state.messages[payload.chatId];
      if (!chat) throw new Error('\u4f1a\u8bdd\u4e0d\u5b58\u5728');
      chat.supportIntervened = true;
      chat.messages.push({
        from: 'system',
        text: '\u5e73\u53f0\u5ba2\u670d\u5df2\u4ecb\u5165\uff0c\u5c06\u7ed3\u5408\u804a\u5929\u8bb0\u5f55\u4e0e\u8ba2\u5355\u4fe1\u606f\u5e2e\u52a9\u534f\u8c03\u3002',
        time: nowString().slice(11, 16)
      });
      return { success: true, chat: clone(chat) };
    }
    case 'getProfile':
      return {
        certification: certificationOverview(),
        orderCount: state.orders.length,
        favoriteCount: state.favorites.length,
        instrumentCount: state.instruments.filter((item) => item.sellerId === state.me.id).length
      };
    case 'getSchoolOptions':
      return schoolOptions();
    case 'submitCertification': {
      if (!payload.name || !payload.phone || !payload.email || !payload.instituteId || !payload.proofName) {
        throw new Error('\u8bf7\u5b8c\u6574\u586b\u5199\u8ba4\u8bc1\u4fe1\u606f');
      }
      if (!validatePhone(payload.phone)) throw new Error('\u624b\u673a\u53f7\u683c\u5f0f\u4e0d\u6b63\u786e');
      if (!validateEmail(payload.email)) throw new Error('\u90ae\u7bb1\u683c\u5f0f\u4e0d\u6b63\u786e');
      const application = {
        id: `cert-${Date.now()}`,
        ...payload,
        status: '\u5f85\u5ba1\u6838',
        submittedAt: nowString()
      };
      state.certificationApplications.unshift(application);
      state.pendingCertification += 1;
      state.me = {
        ...state.me,
        name: payload.name,
        role: payload.role,
        phone: payload.phone,
        email: payload.email,
        instituteId: payload.instituteId,
        school: payload.school,
        college: payload.college,
        proofName: payload.proofName,
        status: '\u5f85\u5ba1\u6838'
      };
      return {
        success: true,
        status: '\u5f85\u5ba1\u6838',
        message:
          '\u8ba4\u8bc1\u4fe1\u606f\u5df2\u63d0\u4ea4\uff0c\u73b0\u5728\u4f1a\u8fdb\u5165\u5b66\u6821/\u673a\u6784\u5ba1\u6838\u6d41\u7a0b\u3002'
      };
    }
    case 'getMyInstruments':
      return { list: clone(state.instruments.filter((item) => item.sellerId === state.me.id)) };
    case 'publishInstrument': {
      ensureVerified('\u53d1\u5e03\u4eea\u5668');
      const tradeModes = normalizeTradeModes(payload.tradeModes, ['\u79df\u8d41']);
      const defaultTradeMode = tradeModes.includes(payload.defaultTradeMode)
        ? payload.defaultTradeMode
        : tradeModes[0];
      const rentPrice = Number(payload.price || 0);
      const salePrice = Number(payload.salePrice || 0);
      const deposit = tradeModes.includes('\u79df\u8d41') ? Number(payload.deposit || 0) : 0;
      const disciplines = String(payload.disciplines || '')
        .split(/[\u3001\uff0c,/\n]+/)
        .map((item) => item.trim())
        .filter(Boolean);
      const breachRules = String(payload.breachRulesText || '')
        .split(/\n+/)
        .map((item) => item.trim())
        .filter(Boolean);
      const damageRules = String(payload.damageRulesText || '')
        .split(/\n+/)
        .map((item) => item.trim())
        .filter(Boolean);
      if (!payload.name || !payload.category || !payload.location || !payload.desc) {
        throw new Error('\u8bf7\u5b8c\u6574\u586b\u5199\u4eea\u5668\u57fa\u7840\u4fe1\u606f');
      }
      if (tradeModes.includes('\u79df\u8d41') && !rentPrice) {
        throw new Error('\u542f\u7528\u79df\u8d41\u6a21\u5f0f\u65f6\uff0c\u8bf7\u586b\u5199\u65e5\u79df\u4ef7');
      }
      if (tradeModes.includes('\u51fa\u552e') && !salePrice) {
        throw new Error('\u542f\u7528\u51fa\u552e\u6a21\u5f0f\u65f6\uff0c\u8bf7\u586b\u5199\u4e70\u65ad\u4ef7');
      }
      const instrument = {
        id: `ins-${Date.now()}`,
        name: payload.name,
        category: payload.category,
        sellerId: state.me.id,
        sellerName: state.me.name,
        sellerRole: state.me.role,
        institute: `${state.me.school} / ${state.me.college}`,
        school: state.me.school,
        college: state.me.college,
        verifiedType: 'blue',
        avatarClass: 'a4',
        posterTheme: 'poster-theme-4',
        location: payload.location,
        phone: state.me.phone,
        email: state.me.email,
        price: rentPrice,
        priceLabel: rentPrice ? asPriceLabel(rentPrice) : '\u4ec5\u652f\u6301\u51fa\u552e',
        salePrice,
        salePriceLabel: salePrice ? `\u00a5${salePrice} \u4e70\u65ad` : '\u4ec5\u652f\u6301\u79df\u8d41',
        tradeModes,
        defaultTradeMode,
        deposit,
        platformServiceFee: 20,
        desc: payload.desc,
        precision: payload.precision || '\u53c2\u6570\u5f85\u8865\u5145',
        disciplines: disciplines.length ? disciplines : ['\u7efc\u5408\u7814\u7a76'],
        withDataPackage: !!payload.withDataPackage,
        remote: !!payload.remote,
        supportInsurance: true,
        availableDates: makeDateRange(24, 7),
        tags: [
          '\u5df2\u8ba4\u8bc1',
          payload.remote ? '\u8fdc\u7a0b\u5b9e\u9a8c' : '\u7ebf\u4e0b\u4ea4\u63a5',
          tradeModes.length === 2 ? '\u79df\u552e\u7686\u53ef' : tradeModes[0]
        ],
        condition: payload.condition || '\u65b0\u53d1\u5e03',
        publishStatus: '\u5df2\u4e0a\u67b6',
        breachRules: breachRules.length
          ? breachRules
          : ['\u8d85\u65f6\u5f52\u8fd8\u6309\u5e73\u53f0\u5408\u540c\u89c4\u5219\u5904\u7406'],
        damageRules: damageRules.length
          ? damageRules
          : ['\u4eba\u4e3a\u635f\u574f\u6309\u68c0\u4fee\u62a5\u4ef7\u8d54\u4ed8'],
        insurancePlans: clone(INSURANCE_PLANS),
        agreementId: AGREEMENT.id,
        servicePackage:
          payload.servicePackage ||
          (payload.withDataPackage ? '\u9644\u5e26\u6570\u636e\u5904\u7406\u8bf4\u660e' : '\u4ec5\u63d0\u4f9b\u4eea\u5668\u4f7f\u7528')
      };
      state.instruments.unshift(instrument);
      return {
        success: true,
        instrumentId: instrument.id,
        message:
          '\u4eea\u5668\u53d1\u5e03\u6210\u529f\uff0c\u5df2\u6309\u201c\u79df\u552e\u53ef\u9009 + \u98ce\u63a7\u4fe1\u606f\u5b8c\u6574\u201d\u7684\u65b9\u5f0f\u4e0a\u67b6\u3002'
      };
    }
    case 'getInstrumentEditDetail':
      return { instrument: clone(getInstrumentById(payload.id)) };
    case 'updateInstrument': {
      const instrument = getInstrumentById(payload.id);
      if (!instrument) throw new Error('\u4eea\u5668\u4e0d\u5b58\u5728');
      const tradeModes = normalizeTradeModes(payload.tradeModes, instrument.tradeModes);
      instrument.tradeModes = tradeModes;
      instrument.defaultTradeMode = tradeModes.includes(payload.defaultTradeMode)
        ? payload.defaultTradeMode
        : tradeModes[0];
      instrument.price = Number(payload.price || 0);
      instrument.priceLabel = instrument.price ? asPriceLabel(Number(payload.price || 0)) : '\u4ec5\u652f\u6301\u51fa\u552e';
      instrument.salePrice = Number(payload.salePrice || 0);
      instrument.salePriceLabel = instrument.salePrice
        ? `\u00a5${instrument.salePrice} \u4e70\u65ad`
        : '\u4ec5\u652f\u6301\u79df\u8d41';
      instrument.deposit = tradeModes.includes('\u79df\u8d41') ? Number(payload.deposit || 0) : 0;
      instrument.location = payload.location;
      instrument.desc = payload.desc;
      instrument.precision = payload.precision || instrument.precision;
      instrument.disciplines = String(payload.disciplines || '')
        .split(/[\u3001\uff0c,/\n]+/)
        .map((item) => item.trim())
        .filter(Boolean);
      instrument.remote = !!payload.remote;
      instrument.withDataPackage = !!payload.withDataPackage;
      instrument.servicePackage = payload.servicePackage || instrument.servicePackage;
      instrument.breachRules = String(payload.breachRulesText || '')
        .split(/\n+/)
        .map((item) => item.trim())
        .filter(Boolean);
      instrument.damageRules = String(payload.damageRulesText || '')
        .split(/\n+/)
        .map((item) => item.trim())
        .filter(Boolean);
      return { success: true, message: '\u4eea\u5668\u4fe1\u606f\u5df2\u66f4\u65b0' };
    }
    case 'getOrderList':
      return {
        list: clone(
          state.orders.map((item) => ({
            ...item,
            instrument: getInstrumentById(item.instrumentId)
          }))
        )
      };
    case 'getOrderDetail': {
      const order = state.orders.find((item) => item.id === payload.id) || state.orders[0];
      return {
        order: clone(order),
        instrument: clone(getInstrumentById(order.instrumentId)),
        agreement: clone(AGREEMENT)
      };
    }
    case 'createDispute': {
      if (!payload.orderId || !payload.summary) {
        throw new Error('\u8bf7\u586b\u5199\u4e89\u8bae\u539f\u56e0');
      }
      const order = state.orders.find((item) => item.id === payload.orderId);
      if (order) {
        order.status = '\u4e89\u8bae\u5904\u7406\u4e2d';
      }
      state.disputes.unshift({
        id: `dispute-${Date.now()}`,
        orderId: payload.orderId,
        summary: payload.summary,
        status: '\u5f85\u5e73\u53f0\u53d7\u7406',
        assignee: '\u5e73\u53f0\u5ba2\u670d 02'
      });
      return { success: true, message: '\u4e89\u8bae\u5df2\u63d0\u4ea4\uff0c\u5e73\u53f0\u5ba2\u670d\u5c06\u5c3d\u5feb\u4ecb\u5165' };
    }
    case 'getFavoriteList':
      return { list: clone(state.instruments.filter((item) => state.favorites.includes(item.id))) };
    case 'getRatingList':
      return { list: clone(state.ratings) };
    case 'publishRating':
      state.ratings.unshift({
        id: `rate-${Date.now()}`,
        orderId: payload.orderId || '\u81ea\u5b9a\u4e49',
        target: payload.target,
        score: Number(payload.score),
        content: payload.content
      });
      return { success: true, message: '\u8bc4\u4ef7\u5df2\u63d0\u4ea4' };
    case 'submitReport':
      if (!payload.targetName || !payload.reason) {
        throw new Error('\u8bf7\u586b\u5199\u4e3e\u62a5\u539f\u56e0');
      }
      state.reports.unshift({
        id: `report-${Date.now()}`,
        targetType: payload.targetType,
        targetName: payload.targetName,
        reason: payload.reason,
        reporter: state.me.name,
        status: '\u5f85\u5904\u7406'
      });
      return { success: true, message: '\u4e3e\u62a5\u5df2\u63d0\u4ea4' };
    case 'getAdminDashboard':
      return {
        pendingCertification: state.certificationApplications.filter((item) => item.status === '\u5f85\u5ba1\u6838').length,
        totalSchools: VERIFIED_SCHOOLS.length,
        totalInstruments: state.instruments.length,
        openDisputes: state.disputes.filter((item) => item.status !== '\u5df2\u7ed3\u6848').length,
        openReports: state.reports.filter((item) => item.status === '\u5f85\u5904\u7406').length
      };
    case 'getSchoolList':
      return { list: schoolOptions() };
    case 'addSchool': {
      const name = String(payload.name || '').trim();
      const colleges = (payload.colleges || [])
        .map((item) => String(item || '').trim())
        .filter(Boolean);
      if (!name || !colleges.length) throw new Error('\u8bf7\u586b\u5199\u5b66\u6821\u4e0e\u5b66\u9662\u4fe1\u606f');
      const existing = VERIFIED_SCHOOLS.find((item) => item.name === name);
      if (existing) {
        existing.colleges = Array.from(new Set(existing.colleges.concat(colleges)));
        return { success: true, message: '\u5df2\u5408\u5e76\u8fdb\u73b0\u6709\u8ba4\u8bc1\u9662\u6821\u5217\u8868' };
      }
      VERIFIED_SCHOOLS.unshift({
        id: `sch-${Date.now()}`,
        name,
        colleges
      });
      return { success: true, message: '\u5b66\u6821 / \u5b66\u9662\u4fe1\u606f\u5df2\u6dfb\u52a0' };
    }
    case 'getCertificationList':
      return { list: clone(state.certificationApplications) };
    case 'reviewCertification': {
      const target = state.certificationApplications.find((item) => item.id === payload.id);
      if (!target) throw new Error('\u7533\u8bf7\u4e0d\u5b58\u5728');
      target.status = payload.status;
      if (target.phone === state.me.phone) {
        state.me.status = payload.status === '\u5df2\u901a\u8fc7' ? '\u5df2\u8ba4\u8bc1' : payload.status;
      }
      if (payload.status !== '\u5f85\u5ba1\u6838') {
        state.pendingCertification = Math.max(0, state.pendingCertification - 1);
      }
      return { success: true, message: '\u8ba4\u8bc1\u5ba1\u6838\u72b6\u6001\u5df2\u66f4\u65b0' };
    }
    case 'getReportList':
      return { list: clone(state.reports) };
    case 'resolveReport': {
      const target = state.reports.find((item) => item.id === payload.id);
      if (!target) throw new Error('\u4e3e\u62a5\u4e0d\u5b58\u5728');
      target.status = '\u5df2\u5904\u7406';
      return { success: true, message: '\u4e3e\u62a5\u5df2\u5904\u7406' };
    }
    case 'getDisputeList':
      return { list: clone(state.disputes) };
    case 'resolveDispute': {
      const target = state.disputes.find((item) => item.id === payload.id);
      if (!target) throw new Error('\u4e89\u8bae\u4e0d\u5b58\u5728');
      target.status = '\u5df2\u7ed3\u6848';
      const order = state.orders.find((item) => item.id === target.orderId);
      if (order) {
        order.status = '\u5e73\u53f0\u5df2\u7ed3\u6848';
      }
      return { success: true, message: '\u4e89\u8bae\u5df2\u7ed3\u6848' };
    }
    case 'getAgreementContent':
      return clone(AGREEMENT);
    default:
      throw new Error(`Unknown mock action: ${action}`);
  }
}

module.exports = {
  invokeMockService,
  APP_NAME
};
