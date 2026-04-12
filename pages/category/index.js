const { callService } = require('../../utils/api');

const CATEGORY_DETAILS = {
  海洋观测: [
    { title: '波浪模拟', icon: '≈', note: '波浪水槽与孔压响应' },
    { title: '沉积分析', icon: '∿', note: '海床沉积与颗粒行为' },
    { title: '环境监测', icon: '○', note: '海水环境参数采集' },
    { title: '时间序列', icon: '↗', note: '长期观测与数据回放' }
  ],
  地质灾害: [
    { title: '边坡稳定', icon: '△', note: '边坡与滑移监测' },
    { title: '振动台', icon: '⌁', note: '动力响应与地震模拟' },
    { title: '土体渗流', icon: '∴', note: '孔压、渗流与冲刷' },
    { title: '监测传感', icon: '⌂', note: '位移、应变与监测布点' }
  ],
  生物材料: [
    { title: '显微表征', icon: '◎', note: '显微结构与形貌观察' },
    { title: '力学测试', icon: '↔', note: '拉伸、压缩与疲劳' },
    { title: '样品制备', icon: '✦', note: '前处理与标准样制备' },
    { title: '数据分析', icon: '⋯', note: '图像与实验数据整理' }
  ],
  化学分析: [
    { title: '光谱检测', icon: '◌', note: '多类光谱分析能力' },
    { title: '成分分析', icon: '◇', note: '元素与组分检测' },
    { title: '标准样', icon: '▣', note: '标准样与校准流程' },
    { title: '结果报告', icon: '≣', note: '检测结果与交付格式' }
  ],
  高精仪器: [
    { title: '高精校准', icon: '✳', note: '精度与稳定性验证' },
    { title: '远程值守', icon: '☰', note: '远程实验与排期值守' },
    { title: '保险方案', icon: '✓', note: '保险与损坏责任约束' },
    { title: '验收交付', icon: '▤', note: '平台验货与过程留痕' }
  ]
};

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '分类加载失败，请稍后重试',
    icon: 'none'
  });
}

function buildDetails(category, schools = []) {
  const items = CATEGORY_DETAILS[category];
  if (items && items.length) return items;
  const fallbackSchool = schools[0];
  const firstCollege = fallbackSchool && fallbackSchool.colleges && fallbackSchool.colleges[0];
  return [
    { title: category, icon: '◦', note: '查看该分类下的全部在架仪器' },
    { title: '认证院校', icon: 'V', note: fallbackSchool ? fallbackSchool.name : '平台认证学校列表' },
    { title: '细分方向', icon: '⋮', note: firstCollege || '进入后继续筛选细分场景' },
    { title: '快速进入', icon: '→', note: '点击任一方向即可进入对应市场页' }
  ];
}

Page({
  data: {
    loading: true,
    categories: [],
    schools: [],
    activeCategory: '',
    categoryDetails: []
  },
  onLoad() {
    this.loadData();
  },
  onShow() {
    this.syncTabBar();
    this.consumePrefillCategory();
  },
  loadData() {
    callService('getCategories')
      .then((res) => {
        const categories = (res.categories || []).filter((item) => item !== '全部');
        const schools = (res.schools || []).map((item) => ({
          ...item,
          collegesText: (item.colleges || []).join(' / ')
        }));
        const activeCategory = categories[0] || '';
        this.setData({
          loading: false,
          categories,
          schools,
          activeCategory,
          categoryDetails: buildDetails(activeCategory, schools)
        });
        this.consumePrefillCategory();
      })
      .catch((error) => {
        this.setData({ loading: false });
        showError(error);
      });
  },
  syncTabBar() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().syncSelected();
    }
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  consumePrefillCategory() {
    const app = getApp();
    const category = app.globalData && app.globalData.prefillCategory;
    if (!category || !this.data.categories.length) return;
    app.globalData.prefillCategory = '';
    this.switchCategory(category);
  },
  switchCategory(category) {
    this.setData({
      activeCategory: category,
      categoryDetails: buildDetails(category, this.data.schools)
    });
  },
  chooseCategory(event) {
    this.switchCategory(event.currentTarget.dataset.category);
  },
  openSubcategory(event) {
    const { category, keyword } = event.currentTarget.dataset;
    wx.navigateTo({
      url: `/pages/equipment/index?category=${encodeURIComponent(category)}&keyword=${encodeURIComponent(keyword || '')}`
    });
  },
  openCategoryMarket() {
    wx.navigateTo({
      url: `/pages/equipment/index?category=${encodeURIComponent(this.data.activeCategory)}`
    });
  }
});
