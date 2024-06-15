from langchain_openai import ChatOpenAI

from prompt_relation import get_relation_prompt, RelationPromptOutputParser

generated_text = """
insert into trading_task (id, created_at, created_by, deleted_at, updated_at, updated_by, assign_time, buy_remainingm, buy_volume, execute_status, expire_date, last_trading_time, sell_remainingm, sell_volume, task_no, traded_volumem, transferred_volumem, ym, assigner_id, buy_currency_id, instruction_id, parent_id, sell_currency_id, trader_id) VALUES (1, '2023-04-01 12:00:00+00', 'user123', NULL, NULL, NULL, '2023-04-02 10:00:00+00', 100.00, 200.00, 'PENDING', '2023-05-01 12:00:00+00', NULL, 150.00, 250.00, 'T123456', 50.00, 30.00, 2023, 101, 201, 301, NULL, 401, 501);
"""

fk_ctx = """
{'trading_task': [1], 'general_user': [1234567890, 1234567891], 'currency': [1], 'instruction': [1], 'hedge_plan_entry': [1], 'company': [1, 2, 1], 'company_currency': [1001], 'hedge_group': [1], 'hedge_plan': [1], 'company_base': [1, 2, 3]}
"""

ddl = """
create table trading_task
(
    id                  bigserial
        primary key,
    created_at          timestamp(6) with time zone,
    created_by          varchar(255),
    deleted_at          timestamp(6) with time zone,
    updated_at          timestamp(6) with time zone,
    updated_by          varchar(255),
    assign_time         timestamp(6) with time zone,
    buy_remainingm      numeric(38, 2) default 0,
    buy_volume          numeric(38, 2) default 0,
    execute_status      varchar(255)
        constraint trading_task_execute_status_check
            check ((execute_status)::text = ANY
                   ((ARRAY ['PENDING'::character varying, 'EXECUTING'::character varying, 'TRADED'::character varying, 'FINISH'::character varying, 'TERMINATED'::character varying])::text[])),
    expire_date         timestamp(6) with time zone,
    last_trading_time   timestamp(6) with time zone,
    sell_remainingm     numeric(38, 2) default 0,
    sell_volume         numeric(38, 2) default 0,
    task_no             varchar(255),
    traded_volumem      numeric(38, 2) default 0,
    transferred_volumem numeric(38, 2) default 0,
    ym                  integer,
    assigner_id         bigint
        constraint "FK6tgsm3fr7e4hu4wnmxvsledsk"
            references general_user,
    buy_currency_id     bigint
        constraint "FKo38epdno2dym6hhrdpejxhmld"
            references currency,
    instruction_id      bigint
        constraint "FKif3lu7ynt87np11o9ya5kixvj"
            references instruction,
    parent_id           bigint
        constraint "FKkuxc8rbd9bmem6d20m7n82wb3"
            references trading_task,
    sell_currency_id    bigint
        constraint "FK33och7vqam3vskgdo10dsb0tt"
            references currency,
    trader_id           bigint
        constraint "FKqjew73xnlvyodk8ngoasc9cj2"
            references general_user
);

comment on table trading_task is '交易任务';

comment on column trading_task.created_at is '实体操作相关信息';

comment on column trading_task.created_by is '实体操作相关信息';

comment on column trading_task.deleted_at is '实体操作相关信息';

comment on column trading_task.updated_at is '实体操作相关信息';

comment on column trading_task.updated_by is '实体操作相关信息';

comment on column trading_task.assign_time is '分配时间';

comment on column trading_task.buy_remainingm is '待买量';

comment on column trading_task.buy_volume is '总买量';

comment on column trading_task.execute_status is '状态';

comment on column trading_task.expire_date is '到期日';

comment on column trading_task.last_trading_time is '最后一次交易的时间';

comment on column trading_task.sell_remainingm is '待卖量';

comment on column trading_task.sell_volume is '总卖量';

comment on column trading_task.task_no is '交易任务编号';

comment on column trading_task.traded_volumem is '已交易量（百万）';

comment on column trading_task.transferred_volumem is '已转交量（百万';

comment on column trading_task.ym is '应执行月份';

comment on column trading_task.assigner_id is '分配者';

comment on column trading_task.buy_currency_id is '买（入币种）';

comment on column trading_task.instruction_id is '套保指令编号';

comment on column trading_task.parent_id is '转交源';

comment on column trading_task.sell_currency_id is '卖（出币种）';

comment on column trading_task.trader_id is '交易员';
"""

llm = ChatOpenAI(model='glm-4-9b-chat',
                 temperature=0,
                 verbose=True,
                 max_tokens=8000,
                 api_key="EMPTY",
                 base_url="http://localhost:8000/v1",
                 )

rel_chain = (get_relation_prompt() | llm | RelationPromptOutputParser())
result = rel_chain.invoke({"stmt": generated_text, "fk_ctx": fk_ctx, "ddl": ddl})
print(result)
optimized = result['modified_statements']
with open('optimized.sql', 'w') as f:
    for i in optimized:
        f.write(i + "\n")
