#!/bin/bash
# Wizard 项目部署脚本
# 使用方法: ./deploy.sh [环境名称]

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取环境参数（默认 dev）
ENV=${1:-dev}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Wizard 项目部署脚本${NC}"
echo -e "${BLUE}  环境: ${ENV}${NC}"
echo -e "${BLUE}========================================${NC}\n"

# 1. 检查是否在项目目录
if [ ! -f "run.py" ]; then
    echo -e "${RED}错误: 请在项目根目录执行此脚本${NC}"
    exit 1
fi

# 2. 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}警告: 虚拟环境不存在，正在创建...${NC}"
    python3 -m venv .venv
fi

# 3. 激活虚拟环境
echo -e "${GREEN}[1/8] 激活虚拟环境${NC}"
source .venv/bin/activate

# 4. 更新代码（如果使用 Git）
if [ -d ".git" ]; then
    echo -e "${GREEN}[2/8] 更新代码${NC}"
    git pull || echo -e "${YELLOW}警告: Git pull 失败，继续部署...${NC}"
else
    echo -e "${YELLOW}[2/8] 跳过 Git 更新（非 Git 仓库）${NC}"
fi

# 5. 安装/更新依赖
echo -e "${GREEN}[3/8] 安装依赖${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 6. 生成 Supervisor 配置
echo -e "${GREEN}[4/8] 生成 Supervisor 配置${NC}"
if [ -f "generate_supervisor_conf.py" ]; then
    python generate_supervisor_conf.py
else
    echo -e "${YELLOW}警告: 找不到 generate_supervisor_conf.py，跳过配置生成${NC}"
fi

# 7. 创建日志目录
echo -e "${GREEN}[5/8] 创建日志目录${NC}"
LOG_DIR="/var/log/wizard"
sudo mkdir -p "$LOG_DIR"
sudo chown $USER:$USER "$LOG_DIR" 2>/dev/null || echo -e "${YELLOW}注意: 可能需要手动设置日志目录权限${NC}"

# 8. 安装 Supervisor 配置文件
echo -e "${GREEN}[6/8] 安装 Supervisor 配置${NC}"
if [ -f "supervisor.conf" ]; then
    sudo cp supervisor.conf /etc/supervisor/conf.d/wizard.conf
    sudo chmod 644 /etc/supervisor/conf.d/wizard.conf
    echo -e "${GREEN}✓ 配置文件已安装${NC}"
else
    echo -e "${RED}错误: 找不到 supervisor.conf 文件${NC}"
    exit 1
fi

# 9. 重新加载 Supervisor 配置
echo -e "${GREEN}[7/8] 重新加载 Supervisor 配置${NC}"
sudo supervisorctl reread
sudo supervisorctl update

# 10. 重启服务
echo -e "${GREEN}[8/8] 重启服务${NC}"
sudo supervisorctl restart wizard

# 等待服务启动
echo -e "${YELLOW}等待服务启动...${NC}"
sleep 3

# 11. 检查状态
echo -e "\n${BLUE}=== 服务状态 ===${NC}"
sudo supervisorctl status wizard

# 12. 显示最近日志
echo -e "\n${BLUE}=== 最近日志（最后 10 行）===${NC}"
sudo supervisorctl tail wizard stdout | tail -10 || echo "暂无日志"

# 完成
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "常用命令:"
echo -e "  查看状态: ${YELLOW}sudo supervisorctl status wizard${NC}"
echo -e "  查看日志: ${YELLOW}sudo supervisorctl tail wizard stdout${NC}"
echo -e "  重启服务: ${YELLOW}sudo supervisorctl restart wizard${NC}"
echo -e "  停止服务: ${YELLOW}sudo supervisorctl stop wizard${NC}"
