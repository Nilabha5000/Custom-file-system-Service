<script>
import { router } from './main';

    export default{
        
        mounted(){
            const item = localStorage.getItem("userCred");
            if(item === null)
               router.push("/signin");
            else{
               router.push("/fs");
            }

        }
    }
</script>

<template>
     <router-view></router-view>
</template>