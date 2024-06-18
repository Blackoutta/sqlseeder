# SQLSeeder: SQL种子数据生成智能体

## 项目简介

研发的小伙伴们，你们是否经常遇到这样的场景：在自测一个刚开发完的接口时，需要向数据库里插入一些测试数据，但是：

1. 有时数据会分散在不同的表，且表与表之间有外键关联关系 这时手动插入所有数据就变得很麻烦。遇到依赖层次多的表关系更是噩梦。
2. 要自己去想每个字段的值填什么，太费脑筋。

本项目就旨在解决这些问题，利用大语言模型的生成能力、ReAct自主推理能力和Tool使用能力来让我们轻松生成测试数据，测试数据越多，后续bug就越少!

## 项目特点

- **真实的数据生成**：利用大语言模型的能力，尽可能让数据看上去真实，不用自己费劲想。
- **从点到面，全面覆盖外键数据**：只需输入一个表名，就可以为所有与目标表有外键关联的表生成数据，不用担心foreign key
  constraint error。
- **错误处理和修正**：如果生成的数据插入失败，Agent会利用大模型的推理能力，根据错误信息和一系列数据库工具来修正SQL语句，确保最终的数据插入成功。

## 目前支持的数据库

- Postgres 13

## 实机演示
抖音: https://v.douyin.com/ijKMdTSk/ 

## 快速开始

1. 克隆仓库：
    ```bash
    git clone https://github.com/Blackoutta/sqlseeder
    cd sqlseeder
    ```

2. 安装所需依赖：
    ```bash
    pip install -r requirements.txt
    ```
3. 本项目使用`glm-4-9b-chat`模型开发完成，但与模型交互使用的是OpenAI的接口，所以可以随时换成你喜欢的模型。

4. 非常建议使用`glm-4-9b-chat`模型，中文英文效果都很好，在没有微调的情况下也能胜任本项目的任务，模型下载地址：
- https://huggingface.co/THUDM/glm-4-9b-chat
- https://modelscope.cn/models/ZhipuAI/glm-4-9b-chat

5. 使用vllm进行模型部署(需在linux环境下进行, 建议使用带GPU的云服务器)：

```bash
pip install vllm

python -m vllm.entrypoints.openai.api_server \
    --model /path/to/model \
    --served-model-name glm-4-9b-chat \
    --dtype bfloat16 \
    --trust-remote-code \
    --port 6006 \
    --host 0.0.0.0 \
    --gpu-memory-utilization 1 \
    --max-model-len 30000
```

6. 用docker-compose启动一个测试数据库

```
version: '3.8'

services:
  postgres:
    image: postgres:latest
    container_name: postgres
    environment:
      POSTGRES_USER: root
      POSTGRES_PASSWORD: root
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres-data:
    driver: local
```

```
docker-compose up -d
```

7. 使用示例数据库建表，示例数据库的dll在test_data/im.txt
8. 启动Agent
```bash
python cli.py --ddl-file test_data/im.txt \
--dbname my_im \
--user root \
--password root \
--host localhost \
--port 5432 \
--loop-cnt 30 \
--model glm-4-9b-chat \
--api-key EMPTY \
--api-base-url http://localhost:6006/v1 \
--temperature 0.0 \
--max-tokens 18000 \
--debug-level=DEBUG
```
---