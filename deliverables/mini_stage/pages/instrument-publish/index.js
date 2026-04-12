const { callService } = require('../../utils/api');

function createTradeModeOptions(selected = ['租赁']) {
  return ['租赁', '出售'].map((value) => ({
    value,
    selected: selected.includes(value)
  }));
}

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '提交失败，请稍后重试',
    icon: 'none'
  });
}

Page({
  data: {
    categories: [],
    categoryIndex: 0,
    tradeModeOptions: createTradeModeOptions(),
    form: {
      name: '',
      price: '',
      salePrice: '',
      deposit: '',
      location: '',
      precision: '',
      disciplines: '',
      servicePackage: '',
      desc: '',
      breachRulesText: '',
      damageRulesText: '',
      withDataPackage: true,
      remote: false
    }
  },
  onLoad() {
    callService('getCategories')
      .then((res) => {
        this.setData({
          categories: res.categories.filter((item) => item !== '全部')
        });
      })
      .catch(showError);
  },
  onShow() {
    this.syncTabBar();
  },
  syncTabBar() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().syncSelected();
    }
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  onInput(event) {
    this.setData({ [`form.${event.currentTarget.dataset.field}`]: event.detail.value });
  },
  onCategoryChange(event) {
    this.setData({ categoryIndex: Number(event.detail.value) });
  },
  toggleTradeMode(event) {
    const mode = event.currentTarget.dataset.mode;
    const selectedModes = this.data.tradeModeOptions
      .filter((item) => item.selected)
      .map((item) => item.value);

    let nextModes = selectedModes.includes(mode)
      ? selectedModes.filter((item) => item !== mode)
      : selectedModes.concat(mode);

    if (!nextModes.length) {
      nextModes = [mode];
    }

    this.setData({
      tradeModeOptions: createTradeModeOptions(nextModes)
    });
  },
  toggleFlag(event) {
    const field = event.currentTarget.dataset.field;
    this.setData({ [`form.${field}`]: !this.data.form[field] });
  },
  submit() {
    const { form, categories, categoryIndex, tradeModeOptions } = this.data;
    const tradeModes = tradeModeOptions.filter((item) => item.selected).map((item) => item.value);

    if (!form.name.trim() || !form.location.trim() || !form.desc.trim()) {
      wx.showToast({ title: '请完善名称、城市和科研描述', icon: 'none' });
      return;
    }
    if (tradeModes.includes('租赁') && !/^\d+(\.\d+)?$/.test(form.price.trim())) {
      wx.showToast({ title: '请填写正确的租赁日价', icon: 'none' });
      return;
    }
    if (tradeModes.includes('出售') && !/^\d+(\.\d+)?$/.test(form.salePrice.trim())) {
      wx.showToast({ title: '请填写正确的买断价格', icon: 'none' });
      return;
    }
    if (tradeModes.includes('租赁') && form.deposit.trim() && !/^\d+(\.\d+)?$/.test(form.deposit.trim())) {
      wx.showToast({ title: '押金格式不正确', icon: 'none' });
      return;
    }

    callService('publishInstrument', {
      ...form,
      category: categories[categoryIndex],
      tradeModes,
      defaultTradeMode: tradeModes[0]
    })
      .then((res) => {
        wx.showModal({
          title: '发布成功',
          content: res.message,
          showCancel: false,
          success: () => {
            wx.navigateTo({ url: '/pages/my-instruments/index' });
          }
        });
      })
      .catch(showError);
  }
});
