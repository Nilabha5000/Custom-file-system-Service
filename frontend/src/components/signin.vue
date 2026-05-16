<script>
    import axios from 'axios';
    import {router} from '@/main';
    export default{
        data(){
            return{
                user : {email : "" , password : ""},
                userInfo : {}
            }

        },
        methods:{
             async usersignin(){

                try{
                    const res = await axios.post("http://localhost:8000/api/signin",this.user);
                    const resData = res.data;
                   console.log(resData)
                    if(resData.status !== "OK"){
                        alert(resData.message);
                    }
                    else{
                        this.userInfo = resData.result;
                        localStorage.setItem("userCred" , JSON.stringify({username : resData.result.username , token : resData.access_token}))
                        router.push("/fs");
                    }
                }
                catch(e){
                    console.log(e)
                }
             }
        }
    }
</script>

<template>
    <div class = "auth-container">
       <div class = "auth-card">
        <h1 class="auth-title">Sign In</h1>
        <v-form @submit.prevent = "usersignin">
        <v-text-field type="text" v-model = "user.email" placeholder="email"/>
        <v-text-field type="password" v-model = "user.password" placeholder="password"/>
        <v-btn color = "primary" type ="submit">Signin</v-btn>
     </v-form>
      <router-link  class = "auth-link" to = '/signup'>If you don't have account then click here </router-link>
    </div>
    </div>
    
     
</template>

<style scoped>
/* ===== Page background (same as fs.vue) ===== */
.auth-container {
  min-height: 100vh;
  width: 100%;

  display: flex;
  justify-content: center;
  align-items: center;

  background: #f6f8fb;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
}

/* ===== Auth card (like file cards) ===== */
.auth-card {
  background: #ffffff;

  width: 100%;
  max-width: 380px;

  padding: 32px 28px;
  border-radius: 16px;

  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.06);

  display: flex;
  flex-direction: column;
  align-items: stretch;
}

/* ===== Title ===== */
.auth-title {
  text-align: center;
  margin-bottom: 22px;

  font-size: 22px;
  font-weight: 600;
  color: #333;
}

/* ===== Vuetify inputs ===== */
.v-text-field {
  margin-bottom: 14px;
}

/* ===== Button ===== */
.v-btn {
  margin-top: 10px;
  height: 42px;

  font-size: 15px;
  font-weight: 500;

  border-radius: 8px;
}

/* ===== Bottom link ===== */
.auth-link {
  margin-top: 18px;

  text-align: center;
  color: #1976d2;

  font-size: 14px;
  text-decoration: underline;

  cursor: pointer;
  transition: 0.2s;
}

.auth-link:hover {
  color: #0d47a1;
}

/* ===== Mobile ===== */
@media (max-width: 420px) {
  .auth-card {
    width: 90%;
    padding: 26px 22px;
  }
}
</style>
