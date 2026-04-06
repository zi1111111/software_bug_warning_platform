import axios, {AxiosInstance, AxiosRequestConfig, AxiosResponse} from 'axios'

//定义基础相应类型
interface BaseResponse <T>{
    code: number;
    data: T;
    message: string;
}

// 扩展请求配置，支持取消请求
interface RequestConfig extends AxiosRequestConfig {
}


class HttpClient {
    private readonly instance: AxiosInstance;
    private baseURL: string;

    constructor(baseURL: string) {
        this.baseURL = baseURL;
        this.instance = axios.create({
            baseURL,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
                // 添加默认认证头
                'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
            },
        });

        this.setupInterceptors();
    }

    private setupInterceptors() {
        // 请求拦截器
        this.instance.interceptors.request.use(
            (config) => {
                // 如果外部已设置则不再重复设置
                if (!config.headers.Authorization) {
                    const token = localStorage.getItem('token');
                    if (token) {
                        config.headers.Authorization = token.startsWith('Bearer ')
                            ? token
                            : `Bearer ${token}`;
                    }
                }
                return config;
            },
            (error) => Promise.reject(error)
        );

        // 响应拦截器
        this.instance.interceptors.response.use(
            (response: AxiosResponse) => {
                // 统一处理响应格式
                return {
                    ...response,
                    data: {
                        code: response.data.code || 0,
                        data: response.data.data || response.data,
                        message: response.data.message || "Success"
                    }
                };
            },
            (error) => {
                // 统一错误处理
                console.error('API Error:', error.response?.data || error.message);
                return Promise.reject(error);
            }
        );
    }
    // 常规请求方法
    public async request<T = any>(config: RequestConfig): Promise<BaseResponse<T>> {
        try {
            const response = await this.instance.request(config);
            return response.data;
        } catch (error: any) {
            // 统一错误格式
            return {
                code: error.response?.status || 500,
                data: null as any,
                message: error.response?.data?.message || error.message || "Unknown error"
            };
        }
    }
    // 简化方法
    public async get<T>(url: string,config?: RequestConfig): Promise<BaseResponse<T>> {
        return this.request<T>({ ...config, method: 'GET', url });
    }

    public async post<T>(url: string, data?: any, config?: RequestConfig): Promise<BaseResponse<T>> {
        return this.request<T>({ ...config, method: 'POST', url, data });
    }

    public async delete<T>(url: string, config?: RequestConfig): Promise<BaseResponse<T>> {
        return this.request<T>({ ...config, method: 'DELETE', url });
    }
}
export const http = new HttpClient("http://localhost:8000");


// 获取漏洞统计
export const getVulnStats = (repo_id: number) => {
    return http.post('/api/getVulnStats', { repo_id })
}

// 获取漏洞列表
export const getVulnerabilities = (params: { repo_id: number, severity?: string, page: number, page_size: number }) => {
    return http.post('/api/getVulnerabilities', params)
}

// 获取漏洞详情
export const getVulnDetail = (vuln_id: number) => {
    return http.post('/api/getVulnDetail', { vuln_id })
}

// 手动触发分析
export const analyzeRepo = (repo_id: number) => {
    return http.post('/api/analyzeRepo', { repo_id })

}