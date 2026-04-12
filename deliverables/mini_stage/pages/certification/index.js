const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '操作失败，请稍后重试',
    icon: 'none'
  });
}

Page({
  data: {
    schools: [],
    schoolNames: [],
    collegeNames: [],
    schoolIndex: 0,
    collegeIndex: 0,
    roleNames: ['科研工作者', '高校教师', '仪器供应方'],
    roleIndex: 0,
    name: '',
    phone: '',
    email: '',
    instituteId: '',
    proofName: '',
    status: '未认证'
  },
  onLoad() {
    Promise.all([callService('getSchoolOptions'), callService('getProfile')])
      .then(([schools, profile]) => {
        const certification = (profile && profile.certification) || {};
        const schoolNames = schools.map((item) => item.name);
        const schoolIndex = Math.max(0, schoolNames.indexOf(certification.school));
        const collegeNames = schools[schoolIndex] ? schools[schoolIndex].colleges || [] : [];
        const collegeIndex = Math.max(0, collegeNames.indexOf(certification.college));
        const roleIndex = Math.max(0, this.data.roleNames.indexOf(certification.role));

        this.setData({
          schools,
          schoolNames,
          collegeNames,
          schoolIndex,
          collegeIndex,
          roleIndex,
          name: certification.name === '未认证用户' ? '' : certification.name || '',
          phone: certification.phone || '',
          email: certification.email || '',
          instituteId: certification.instituteId || '',
          proofName: certification.proofName || '',
          status: certification.status || '未认证'
        });
      })
      .catch(showError);
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  onInput(event) {
    this.setData({ [event.currentTarget.dataset.field]: event.detail.value });
  },
  onRoleChange(event) {
    this.setData({ roleIndex: Number(event.detail.value) });
  },
  onSchoolChange(event) {
    const schoolIndex = Number(event.detail.value);
    this.setData({
      schoolIndex,
      collegeIndex: 0,
      collegeNames: (this.data.schools[schoolIndex] && this.data.schools[schoolIndex].colleges) || []
    });
  },
  onCollegeChange(event) {
    this.setData({ collegeIndex: Number(event.detail.value) });
  },
  mockUploadProof() {
    this.setData({ proofName: 'institution-proof.pdf' });
    wx.showToast({ title: '已模拟上传证明', icon: 'none' });
  },
  resetCertification() {
    wx.showModal({
      title: '重置认证',
      content: '这会清空当前账号的认证信息，并恢复为未认证状态。确认继续吗？',
      success: ({ confirm }) => {
        if (!confirm) return;
        callService('resetCurrentUserCertification')
          .then((res) => {
            wx.showToast({ title: res.message, icon: 'none' });
            this.setData({
              roleIndex: 0,
              name: '',
              phone: '',
              email: '',
              instituteId: '',
              proofName: '',
              status: res.status,
              schoolIndex: 0,
              collegeIndex: 0,
              collegeNames: (this.data.schools[0] && this.data.schools[0].colleges) || []
            });
          })
          .catch(showError);
      }
    });
  },
  submit() {
    const {
      name,
      phone,
      email,
      instituteId,
      proofName,
      roleNames,
      roleIndex,
      schoolNames,
      collegeNames,
      schoolIndex,
      collegeIndex
    } = this.data;

    if (!name.trim() || !phone.trim() || !email.trim() || !instituteId.trim() || !proofName.trim()) {
      wx.showToast({ title: '请完整填写认证信息', icon: 'none' });
      return;
    }
    if (!schoolNames.length || !collegeNames.length) {
      wx.showToast({ title: '请先选择学校和学院', icon: 'none' });
      return;
    }
    if (!/^1\d{10}$/.test(phone.trim())) {
      wx.showToast({ title: '请输入正确手机号', icon: 'none' });
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      wx.showToast({ title: '请输入正确邮箱', icon: 'none' });
      return;
    }

    callService('submitCertification', {
      name: name.trim(),
      phone: phone.trim(),
      email: email.trim(),
      instituteId: instituteId.trim(),
      proofName: proofName.trim(),
      role: roleNames[roleIndex],
      school: schoolNames[schoolIndex],
      college: collegeNames[collegeIndex]
    })
      .then((res) => {
        this.setData({ status: res.status });
        wx.showModal({ title: '提交成功', content: res.message, showCancel: false });
      })
      .catch(showError);
  }
});
