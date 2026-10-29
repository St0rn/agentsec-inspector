import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";

export function useApi<T>(path:string){const [data,setData]=useState<T>();const [error,setError]=useState("");const [loading,setLoading]=useState(true);const reload=useCallback(async()=>{setLoading(true);setError("");try{setData(await api<T>(path))}catch(e){setError(e instanceof Error?e.message:String(e))}finally{setLoading(false)}},[path]);useEffect(()=>{void reload()},[reload]);return{data,error,loading,reload,setData}}
