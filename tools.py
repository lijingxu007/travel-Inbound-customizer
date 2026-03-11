import os
import requests
from typing import List, Optional, Dict, Any

# 飞书 API 基础配置
FEISHU_API_BASE = "https://open.feishu.cn/open-apis"

def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    # ... (保持不变)
    url = f"{FEISHU_API_BASE}/auth/v3/tenant_access_token/internal"
    payload = { "app_id": app_id, "app_secret": app_secret }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get('code') != 0:
            raise Exception(f"Feishu Auth Failed: {data.get('msg')}")
        return data['tenant_access_token']
    except Exception as e:
        raise Exception(f"Network or Auth Error: {str(e)}")

def submit_inbound_lead(
    name: str,
    contact: str,          # 改为 contact，兼容邮箱和电话
    nationality: str,      # 新增：国籍
    destinations: str,     # 意向目的地
    group_size: int,       # 人数
    travel_dates: Optional[str] = "", # 改为 travel_dates，更灵活
    budget: Optional[float] = 0.0,
    currency: Optional[str] = "CNY", # 新增：货币类型
    interests: Optional[List[str]] = None,
    language_pref: Optional[str] = "English", # 新增：语言偏好
    special_requirements: Optional[str] = ""
) -> Dict[str, Any]:
    """
    ClawHub 工具函数：将入境游线索提交到飞书多维表格
    """
    # 从环境变量读取配置
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    base_token = os.getenv("FEISHU_BASE_TOKEN")
    table_id = os.getenv("FEISHU_TABLE_ID")
    
    # 校验配置
    missing_configs = []
    if not app_id: missing_configs.append("FEISHU_APP_ID")
    if not app_secret: missing_configs.append("FEISHU_APP_SECRET")
    if not base_token: missing_configs.append("FEISHU_BASE_TOKEN")
    if not table_id: missing_configs.append("FEISHU_TABLE_ID")
    
    if missing_configs:
        return { "status": "error", "message": f"Missing config: {', '.join(missing_configs)}" }
    
    try:
        # 1. 获取 Token
        token = get_tenant_access_token(app_id, app_secret)
        
        # 2. 构建字段映射 (请确保飞书表格中创建了以下对应列名)
        # 建议飞书列名：姓名, 联系方式, 国籍, 意向目的地, 出行人数, 预计行程时间, 人均预算, 货币单位, 兴趣偏好, 语言需求, 特殊备注
        fields = {
            "姓名": name,
            "联系方式": contact,
            "国籍": nationality,
            "意向目的地": destinations,
            "出行人数": group_size,
            "语言需求": language_pref
        }
        
        if travel_dates:
            fields["预计行程时间"] = travel_dates
        
        if budget and budget > 0:
            fields["人均预算"] = budget
            fields["货币单位"] = currency
            
        if interests and len(interests) > 0:
            # 飞书多选字段通常需要列表，单行文本则 join
            fields["兴趣偏好"] = ", ".join(interests) if isinstance(interests, list) else interests
            
        if special_requirements:
            fields["特殊备注"] = special_requirements
            
        # 3. 调用飞书新增记录 API
        url = f"{FEISHU_API_BASE}/bitable/v1/apps/{base_token}/tables/{table_id}/records"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = { "records": [{ "fields": fields }] }
        
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        
        if result.get('code') == 0:
            return {"status": "success", "message": "Lead submitted successfully!"}
        else:
            return {"status": "error", "message": f"Feishu API Error: {result.get('msg')}"}
            
    except Exception as e:
        return {"status": "error", "message": f"System Exception: {str(e)}"}

if __name__ == "__main__":
    print("Inbound Travel Tools module loaded.")