<template>
  <view class="page-shell">
    <view class="hero-panel">
      <view class="hero-tag">个人认证</view>
      <view class="hero-title">科研身份认证</view>
      <view class="hero-copy">这里只有一条主操作线：填写资料并提交审核。重置资料不再做成第二个大按钮。</view>
    </view>

    <view class="section">
      <view class="card panel cert-panel">
        <view class="status-note">未认证用户先填写资料并提交审核，提交后等待平台人工核验。</view>

        <view class="form-label">姓名</view>
        <input v-model="form.name" class="form-input" placeholder="请输入姓名" />

        <view class="form-label top-gap">角色</view>
        <input v-model="form.role" class="form-input" placeholder="科研工作者 / 高校教师 / 仪器供应方" />

        <view class="form-label top-gap">电话</view>
        <input v-model="form.phone" class="form-input" placeholder="请输入手机号" />

        <view class="form-label top-gap">邮箱</view>
        <input v-model="form.email" class="form-input" placeholder="请输入机构邮箱" />

        <view class="form-label top-gap">学工号 / 工号</view>
        <input v-model="form.instituteId" class="form-input" placeholder="请输入学工号或工号" />

        <view class="form-label top-gap">学校</view>
        <picker :range="schoolNames" :value="schoolIndex" @change="onSchoolChange">
          <view class="picker-box">{{ schoolNames[schoolIndex] || '请选择学校' }}</view>
        </picker>

        <view class="form-label top-gap">学院</view>
        <picker :range="collegeNames" :value="collegeIndex" @change="onCollegeChange">
          <view class="picker-box">{{ collegeNames[collegeIndex] || '请选择学院' }}</view>
        </picker>

        <view class="form-label top-gap">机构证明</view>
        <input v-model="form.proofName" class="form-input" placeholder="填写证明文件名称" />

        <view class="primary-btn full-btn top-gap" @tap="submit">提交认证</view>
        <view class="minor-action" @tap="reset">清空资料并恢复未认证</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { callService } from '../../common/service'

const form = reactive({
  name: '',
  role: '科研工作者',
  phone: '',
  email: '',
  instituteId: '',
  school: '',
  college: '',
  proofName: ''
})
const schools = ref([])
const schoolNames = ref([])
const collegeNames = ref([])
const schoolIndex = ref(0)
const collegeIndex = ref(0)

onMounted(async () => {
  const categoryRes = await callService('getCategories')
  schools.value = categoryRes.schools
  schoolNames.value = schools.value.map((item) => item.name)
  if (schools.value[0]) {
    collegeNames.value = schools.value[0].colleges
  }
  const profile = await callService('getProfile')
  Object.assign(form, profile.certification)
  syncPickerFromForm()
})

function syncPickerFromForm() {
  const nextSchoolIndex = Math.max(0, schoolNames.value.indexOf(form.school))
  schoolIndex.value = nextSchoolIndex
  collegeNames.value = (schools.value[nextSchoolIndex] && schools.value[nextSchoolIndex].colleges) || []
  const nextCollegeIndex = Math.max(0, collegeNames.value.indexOf(form.college))
  collegeIndex.value = nextCollegeIndex
  form.school = schoolNames.value[nextSchoolIndex] || ''
  form.college = collegeNames.value[nextCollegeIndex] || ''
}

function onSchoolChange(event) {
  schoolIndex.value = Number(event.detail.value)
  form.school = schoolNames.value[schoolIndex.value]
  collegeNames.value = schools.value[schoolIndex.value].colleges
  collegeIndex.value = 0
  form.college = collegeNames.value[0] || ''
}

function onCollegeChange(event) {
  collegeIndex.value = Number(event.detail.value)
  form.college = collegeNames.value[collegeIndex.value]
}

async function submit() {
  await callService('submitCertification', form)
  uni.showToast({ title: '认证已提交', icon: 'success' })
}

async function reset() {
  await callService('resetCertification')
  Object.assign(form, {
    name: '',
    role: '科研工作者',
    phone: '',
    email: '',
    instituteId: '',
    school: '',
    college: '',
    proofName: ''
  })
  syncPickerFromForm()
  uni.showToast({ title: '已重置', icon: 'success' })
}
</script>

<style scoped lang="scss">
.cert-panel {
  padding-bottom: 34rpx;
}

.status-note {
  margin-bottom: 24rpx;
  padding: 20rpx 22rpx;
  border-radius: 22rpx;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.08) 0%, rgba(247, 247, 248, 0.92) 100%);
  color: #4b5563;
  font-size: 22rpx;
  line-height: 1.75;
}

.minor-action {
  padding-top: 20rpx;
  text-align: center;
  color: #64748b;
  font-size: 24rpx;
  line-height: 1.8;
}
</style>
