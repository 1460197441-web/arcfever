const { callService } = require('../../utils/api');

Page({
  data: {
    schools: [],
    schoolNames: [],
    collegeNames: [],
    schoolIndex: 0,
    collegeIndex: 0,
    name: '',
    phone: ''
  },
  onLoad() {
    callService('getSchoolOptions').then((schools) => {
      this.setData({
        schools,
        schoolNames: schools.map((item) => item.name),
        collegeNames: schools[0].colleges
      });
    });
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  onInput(event) {
    this.setData({ [event.currentTarget.dataset.field]: event.detail.value });
  },
  onSchoolChange(event) {
    const schoolIndex = Number(event.detail.value);
    this.setData({
      schoolIndex,
      collegeIndex: 0,
      collegeNames: this.data.schools[schoolIndex].colleges
    });
  },
  onCollegeChange(event) {
    this.setData({ collegeIndex: Number(event.detail.value) });
  },
  submit() {
    const { name, phone, schoolNames, collegeNames, schoolIndex, collegeIndex } = this.data;
    if (!name.trim() || !phone.trim()) {
      wx.showToast({ title: '请填写姓名和电话', icon: 'none' });
      return;
    }
    callService('submitCertification', {
      name,
      phone,
      school: schoolNames[schoolIndex],
      college: collegeNames[collegeIndex]
    }).then((res) => {
      wx.showModal({ title: '提交成功', content: res.message, showCancel: false });
    });
  }
});
