const { callService } = require('../../utils/api');

Page({
  data: {
    categories: [],
    categoryIndex: 0,
    form: {
      name: '',
      price: '',
      location: '',
      desc: ''
    }
  },
  onLoad() {
    callService('getCategories').then((res) => {
      this.setData({ categories: res.categories.filter((item) => item !== '全部') });
    });
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
  submit() {
    const { form, categories, categoryIndex } = this.data;
    if (!form.name.trim() || !form.price.trim()) {
      wx.showToast({ title: '请填写仪器名称和价格', icon: 'none' });
      return;
    }
    callService('publishInstrument', {
      ...form,
      category: categories[categoryIndex]
    }).then((res) => {
      wx.showModal({ title: '发布成功', content: res.message, showCancel: false });
    });
  }
});
