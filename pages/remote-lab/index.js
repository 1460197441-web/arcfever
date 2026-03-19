const { callService } = require('../../utils/api');

Page({
  data: {
    packages: [
      {
        title: '标准代测',
        price: '1999 元起',
        desc: '适合单次实验验证，提供原始数据、实验记录和简版分析。'
      },
      {
        title: '项目联测',
        price: '6999 元起',
        desc: '适合阶段性科研任务，支持多轮实验和统一数据报告。'
      },
      {
        title: '企业定制',
        price: '按方案报价',
        desc: '适合企业研发外包与复杂场景，配套工程师与交付管理。'
      }
    ],
    fields: {
      topic: '',
      contact: '',
      requirement: ''
    }
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  onInput(event) {
    const { field } = event.currentTarget.dataset;
    this.setData({
      [`fields.${field}`]: event.detail.value
    });
  },
  submitRequest() {
    const { topic, contact, requirement } = this.data.fields;
    if (!topic.trim() || !contact.trim()) {
      wx.showToast({ title: '请完善主题与联系方式', icon: 'none' });
      return;
    }
    callService('createOrder', {
      mode: '远程实验咨询',
      topic,
      contact,
      requirement
    }).then((res) => {
      wx.showModal({
        title: '远程实验需求已提交',
        content: `${res.message}\n订单号：${res.orderNo}`,
        showCancel: false
      });
    });
  },
  goEquipment() {
    wx.navigateTo({ url: '/pages/equipment/index' });
  }
});
