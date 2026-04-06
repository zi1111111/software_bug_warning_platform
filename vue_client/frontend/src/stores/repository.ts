import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {RepositoriesData, Repository} from "../response/response";
import {http} from "../request/request";

export const useRepoStore = defineStore('repository' ,() => {
  // State

  const repositories = ref<Repository[]>([])

  const fetchRepositories = async () => {
    const res = await http.get<RepositoriesData>("/api/getAllRepositories")
    repositories.value = res.data.repositories
    console.log(repositories.value)
  }

  fetchRepositories().then(r => {})

  const currentRepoId = ref(1)
  // Getters
  const currentRepo = computed(() => {
    return repositories.value.find(r => r.id === currentRepoId.value) || repositories.value[0]
  })

  const activeRepos = computed(() => {
    return repositories.value.filter(r => r.is_active === true)
  })


  // Actions
  const setCurrentRepo = (repoId:number) => {
    currentRepoId.value = repoId
    // 更新所有仓库的 active 状态
    repositories.value.forEach(r => {
      r.is_active = (r.id === repoId)
    })
  }

  const addRepository = async (
    data:{
      name : string
      repo_url : string
      default_branch : string
      is_active : boolean}) =>
  {
    const res = await http.post("/api/addRepository", data)
    if(res.code===200){
      console.log(res.message)
      fetchRepositories().then(r => {})
      return true
    }
    return false
  }

  const changeRepository = async(
      data:{
        id:number,
        default_branch : string
        is_active : boolean
      }) =>
  {
    const res = await http.post("/api/changeRepository", data)
    if(res.code===200){
      console.log(res.message)
      fetchRepositories().then(r => {})
      return true
    }
    return false
  }

  const deleteRepository = async (data:{
    id:number
  }) =>
  {
    const res = await http.post("/api/deleteRepository", data)
    if(res.code===200){
      console.log(res.message)
      return true
    }
    return false
  }


  return {
    repositories,
    currentRepoId,
    currentRepo,
    activeRepos,
    setCurrentRepo,
    addRepository,
    changeRepository,
    deleteRepository,
    fetchRepositories
  }
})
