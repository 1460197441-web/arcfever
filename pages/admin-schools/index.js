const { callService } = require('../../utils/api');

Page({
  data: {
    list: [],
    schoolName: '',
    collegesText: ''
  },
  onShow() {
    this.loadData();
  },
  loadData() {
    callService('getSchoolList').then((res) => this.setData({ list: res.list }));
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  onInput(event) {
    this.setData({ [event.currentTarget.dataset.field]: event.detail.value });
  },
  submit() {
    if (!this.data.schoolName.trim() || !this.data.collegesText.trim()) {
      wx.showToast({ title: '请填写学校和学院', icon: 'none' });
      return;
    }
    callService('addSchool', {
      name: this.data.schoolName,
      colleges: this.data.collegesText.split('、')
    }).then((res) => {
      wx.showModal({ title: '添加成功', content: res.message, showCancel: false });
      this.setData({ schoolName: '', collegesText: '' });
    });
  }
});
