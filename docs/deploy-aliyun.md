---
title: 在阿里云部署工具合规扫描 Agent（容器化 + 自动化）
version: 0.1
status: draft
date: 2026-02-10
---

## 1. 总体方案

本部署方案基于：

- **容器化应用**：使用项目根目录的 `Dockerfile` 构建镜像；
- **阿里云容器镜像服务 ACR**：存放镜像；
- **阿里云 ECS（或 ACK 集群上的节点）**：运行容器（示例使用 ECS + Docker Compose）；
- **GitHub Actions**：在 push 到 `main` 时自动构建并推送镜像，可选地通过 SSH 触发 ECS 上的更新。

> 说明：下面使用占位符名称，请根据实际环境替换，如：\
> `registry.cn-hangzhou.aliyuncs.com/your-namespace/tool-compliance-scanning`

---

## 2. 容器镜像构建（本地验证）

1. 在项目根目录执行：

```bash
docker build -t tool-compliance-scanning:local .
```

2. 本地运行（示例）：

```bash
docker run --rm -p 8080:8080 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -e CONFIG_PATH=/app/config/config.yaml \
  tool-compliance-scanning:local
```

浏览器访问 `http://localhost:8080/ui` 验证服务是否正常。

---

## 3. 推送到阿里云容器镜像服务 ACR

1. 在阿里云控制台创建容器镜像仓库，例如：

- 区域：`cn-hangzhou`
- 命名空间：`your-namespace`
- 仓库名称：`tool-compliance-scanning`

2. 本地登录并推送（示意）：

```bash
docker login registry.cn-hangzhou.aliyuncs.com

docker tag tool-compliance-scanning:local \
  registry.cn-hangzhou.aliyuncs.com/your-namespace/tool-compliance-scanning:latest

docker push registry.cn-hangzhou.aliyuncs.com/your-namespace/tool-compliance-scanning:latest
```

实际环境中建议通过 GitHub Actions 自动完成，见下一节。

---

## 4. GitHub Actions 自动构建与推送镜像

在仓库中创建 `.github/workflows/deploy-aliyun.yml`（本项目已提供示例模板），其核心逻辑：

- 在 push 到 `main` 分支时：
  - `checkout` 代码；
  - 登录阿里云 ACR（使用仓库 Secrets：`ALIYUN_REGISTRY`, `ALIYUN_REGISTRY_USERNAME`, `ALIYUN_REGISTRY_PASSWORD`）；
  - 使用 `Dockerfile` 构建镜像并推送到 ACR；
  - 可选：通过 SSH 登录 ECS，执行 `docker pull` + `docker compose up -d` 完成滚动更新。

> 在 GitHub 仓库 Settings → Secrets and variables → Actions 中配置：\
> `ALIYUN_REGISTRY`（如 `registry.cn-hangzhou.aliyuncs.com`）\
> `ALIYUN_REGISTRY_NAMESPACE`（命名空间）\
> `ALIYUN_REGISTRY_REPO`（仓库名，如 `tool-compliance-scanning`）\
> `ALIYUN_REGISTRY_USERNAME` / `ALIYUN_REGISTRY_PASSWORD`\
> （如需自动部署到 ECS）`ALIYUN_ECS_HOST`, `ALIYUN_ECS_USER`, `ALIYUN_ECS_SSH_KEY`

### 4.1 使用 RAM 用户（子账号）做 CI/CD

若使用 RAM 用户（如 `ram-user-for-tool-compliance-scan`）专门做构建与推送，按以下步骤操作即可，无需主账号密码。

1. **权限**  
   RAM 用户需具备 ACR 访问权限。若已授予系统策略 `PowerUserAccess`，已包含容器镜像服务权限，可直接进行下一步。若希望最小权限，可改为授予 `AliyunContainerRegistryFullAccess` 或自定义策略（包含 `cr:GetAuthorizationToken`、`cr:PullRepository`、`cr:PushRepository` 等）。

2. **ACR 访问凭证（必做）**  
   Docker 登录 ACR 使用的是「镜像仓库登录用户名 + 密码」，不是 AccessKey。
   - 使用该 RAM 用户登录 [阿里云控制台](https://ram.console.aliyun.com/users)，进入 **容器镜像服务 ACR**。
   - 在左侧进入 **访问凭证**，为该 RAM 用户设置 **固定密码**（无时效，适合 CI/CD）。
   - 页面上会给出示例命令，例如：  
     `docker login registry.cn-hangzhou.aliyuncs.com --username=ram-user-for-tool-compliance-scan@1060904592004128.onaliyun.com`  
     提示输入密码时，输入上一步设置的固定密码。

3. **GitHub Secrets 填写**  
   - `ALIYUN_REGISTRY`：登录地址，建议用 **默认公网地址** `registry.cn-hangzhou.aliyuncs.com`（个人版实例域名若在公网解析不到，CI 会报 NXDOMAIN）。
   - `ALIYUN_REGISTRY_NAMESPACE` / `ALIYUN_REGISTRY_REPO`：你在 ACR 创建的命名空间和仓库名。
   - `ALIYUN_REGISTRY_USERNAME`：**ACR 访问凭证中的用户名**（即上一步 `docker login --username=` 的值，通常是 RAM 用户完整登录名，如 `ram-user-for-tool-compliance-scan@1060904592004128.onaliyun.com`）。
   - `ALIYUN_REGISTRY_PASSWORD`：**该 RAM 用户在 ACR 中设置的固定密码**。  
   **不要** 使用 AccessKey ID / AccessKey Secret 作为用户名或密码，否则会报 `unauthorized: authentication required`。

4. **本地验证（可选）**  
   在 WSL 或 PowerShell 中执行（将用户名和密码替换为上面 ACR 凭证）：  
   `docker login registry.cn-hangzhou.aliyuncs.com -u "<ACR 用户名>" -p "<ACR 固定密码>"`  
   登录成功后，再 push 到对应命名空间/仓库，即可确认该 RAM 用户权限与凭证正确。

---

## 5. ECS 上的运行（Docker Compose 示例）

在 ECS 实例上（建议目录 `/opt/tool-compliance-scanning`）创建 `docker-compose.yml`：

```yaml
version: "3.9"
services:
  tool-compliance:
    image: registry.cn-hangzhou.aliyuncs.com/your-namespace/tool-compliance-scanning:latest
    container_name: tool-compliance-scanning
    restart: always
    ports:
      - "8080:8080"
    environment:
      - CONFIG_PATH=/config/config.yaml
    volumes:
      - /opt/tool-compliance-scanning/config:/config
      - /opt/tool-compliance-scanning/data:/data
      - /opt/tool-compliance-scanning/logs:/logs
```

首次部署时：

```bash
mkdir -p /opt/tool-compliance-scanning/{config,data,logs}
cp /path/on/ecs/config.yaml /opt/tool-compliance-scanning/config/config.yaml  # 放入实际配置

docker login registry.cn-hangzhou.aliyuncs.com
docker compose -f /opt/tool-compliance-scanning/docker-compose.yml pull
docker compose -f /opt/tool-compliance-scanning/docker-compose.yml up -d
```

之后每次 CI/CD 推送新镜像后，只需在 ECS 上执行：

```bash
docker compose -f /opt/tool-compliance-scanning/docker-compose.yml pull
docker compose -f /opt/tool-compliance-scanning/docker-compose.yml up -d
```

（可由 GitHub Actions 通过 SSH 自动执行。）

---

## 6. 可选：阿里云 ACK 集群部署

如果使用 **阿里云容器服务 ACK**，可基于上述镜像编写 Kubernetes Deployment/Service 清单，并通过：

- 在 GitHub Actions 中配置 `kubectl` + Kubeconfig；
- 或在本地使用 `kubectl apply -f deployment.yaml`；

将服务部署到集群内，暴露为 LoadBalancer / Ingress。

---

## 7. 配置要点回顾

- `config/config.yaml` 中的：\n
  - `service.port` 控制 Web 端口（容器内仍 EXPOSE 8080，外部端口映射可随意）；\n
  - `ai.glm.api_key` 必须在云环境中填入有效 GLM Key；\n
  - `database` 段可按需切换为云 MySQL 或继续使用 SQLite 文件卷挂载。\n
- 日志与数据目录建议挂载到 ECS 主机（或云盘），避免容器销毁导致数据丢失。

