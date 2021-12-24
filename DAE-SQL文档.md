[TOC]


# SQL 功能介绍&使用手册
数据导入、数据查询、表操作等 CK 常见和最可能被用户用到的 基础功能

## 1. 快速入门案例

DAE SQL是一款面向大数据的、旨在提供对结构化数据使用SQL语句进行查询、分析、统计等功能的单机计算引擎，提供了数据导入、导出能力，和DAE的其他两大模块DataFrame和ML能够无缝对接。  

下面将介绍SQL引擎基本功能的使用方式，目前SQL引擎支持python api,用户可以通过编写python程序实现和引擎的交互。

### 1.1  三分钟入门

构建csv文件，建表查询
```python
#构建csv文件
import os
with open('./test.csv', 'w+') as f:
    f.write('''name,age,fee
               Tom,32,3205.0
               Jack,31,14523.0
               Herry,28,9845.0''') 
               
#建表并查询
from dae import sql
sql("create table table1 from 'test.csv' format CSV")
sql("select * from table1 where age > 30").show()
```

    name      age    salary
    ------  -----  --------
    Tom        32     13205
    Jack       31     14523

其他功能简介
```python
#查外部数据（HIVE/HDFS/MySQL/MongoDB/PostgreSQL/BOS/Iceberg等）
sql("CREATE TABLE hdfs_table (name String, value UInt32) ENGINE=HDFS('hdfs://hdfs1:9000/other_storage', 'Parquet')")

#查询结果可cache到本地，供后续复用
search_res = sql("select * from table1 where age > 30")
search_res.cache()  #cache计算结果
sql("select * from {search_res}").show()

#多个交互sql组成 复杂sql，整体执行优化
t1 = sql('SELECT * FROM system.tables')
t2 = sql('SELECT * FROM system.columns')
t3 = sql("SELECT * FROM {t1} as t1 JOIN {t2} as t2 ON(t1.name=t2.table) limit 1").show()

#sql与dataframe混合使用
df = sql("select * from table1 where age > 10").to_df()  #sql table转成dataframe
df = df[df.age > 30]  #dataframe计算
sql("select * from {df}").show()  #sql中直接使用dataframe对象
```

### 1.2 导入SQL依赖，建表并导入数据

本教程将使用以下方式导入SQL依赖:


```python
from dae import sql
```

我们先生成如下一份数据文件"test.csv", 数据每行包含3个字段:  


|  列名   | 说明  | 类型  |
|  ----  | ----  | ----  |
|  user | 姓名 | String |
| age | 年龄 | Int32 |
| fee  | 费用 | Float32 |


```python
import os
data_path='./test.csv'
file = open(data_path, 'w+')
file.write('''Tom,32,13205.0
              Jack,31,14523.0
              Herry,28,9845.0
              Bob,43,28314.0
              Alice,23,7854.0''')
file.close()
```

建表前为了保证数据不受污染,首先清理可能存在的同名的表,代码如下:


```python
table_name='test'
sql('drop table if exists {table_name}')
```



下面我们将使用上面代码生成的数据文件来建表并导入数据,表名称为'test',代码如下:  


```python
data_schema = '''user String,age Int32,fees Float32'''
ds = sql("create table if not exists {table_name} ({data_schema}) Engine=MergeTree() order by tuple()")
```


### 1.3 查看表并导入数据


```python
sql("show tables").show()
```

    name
    ------
    test



```python
sql("insert into table {table_name} from infile '{path}' format CSV", path=data_path)
```


### 1.4 开始查询

#### 1.4.1 全量查询表中的数据


```python
sql('select * from test').show()
```

    user      age    fees
    ------  -----  ------
    Tom        32   13205
    Jack       31   14523
    Herry      28    9845
    Bob        43   28314
    Alice      23    7854

#### 1.4.2 设置条件进行查询(过滤)


```python
sql('select * from test where fees < 10000.0 limit 2').show()
```

    user      age    fees
    ------  -----  ------
    Herry      28    9845
    Alice      23    7854

#### 1.4.3 对某列求和/求算术平均/最大/最小值


```python
sql('select sum(fees) from test').show()
sql('select avg(age) from test').show()
sql('select min(age) from test').show()
sql('select max(fees) from test').show()
```

      sum(fees)
    -----------
          73741
      avg(age)
    ----------
          31.4
      min(age)
    ----------
            23
      max(fees)
    -----------
          28314

#### 1.4.4 排序


```python
sql('select * from test order by age desc').show()
```

    user      age    fees
    ------  -----  ------
    Bob        43   28314
    Tom        32   13205
    Jack       31   14523
    Herry      28    9845
    Alice      23    7854

#### 1.4.5 聚合


```python
sql('select user, max(fees) from test group by user').show()
```

    user      max(fees)
    ------  -----------
    Alice          7854
    Tom           13205
    Herry          9845
    Bob           28314
    Jack          14523

#### 1.4.6 查询结果导出到文件

目前导出的文件格式为tsv(即以tab符分隔字段的文件)
```python
sql("select age, sum(fees) from test group by age into outfile './result.tsv' format TSV").show()
```


## 2. 基本功能介绍
### 2.1 数据类型定义
#### 2.1.1 数值类型
**2.1.1.1 Int类型**
	
	固定长度的整数类型又包括有符号和无符号的整数类型。
	
	有符号整数类型
	Int8	1	[-2^7 ~2^7-1]
	Int16	2	[-2^15 ~ 2^15-1]
	Int32	4	[-2^31 ~ 2^31-1]
	Int64	8	[-2^63 ~ 2^63-1]
	Int128	16	[-2^127 ~ 2^127-1]
	Int256	32	[-2^255 ~ 2^255-1]
	
	无符号类型
	UInt8	1	[0 ~2^8-1]
	UInt16	2	[0 ~ 2^16-1]
	UInt32	4	[0 ~ 2^32-1]
	UInt64	8	[0 ~ 2^64-1]
	UInt256	32	[0 ~ 2^256-1]

**2.1.1.2 浮点类型**
单精度浮点数
Float32从小数点后第8位起会发生数据溢出

	Float32

双精度浮点数
Float32从小数点后第17位起会发生数据溢出

	Float64

**2.1.1.3 Decimal类型**
有符号的定点数，可在加、减和乘法运算过程中保持精度。此处提供了Decimal32、Decimal64和Decimal128三种精度的定点数，支持几种写法：

	Decimal(P, S)
	Decimal32(S)
	数据范围：( -1 * 10^(9 - S), 1 * 10^(9 - S) )
	Decimal64(S)
	数据范围：( -1 * 10^(18 - S), 1 * 10^(18 - S) )
	Decimal128(S)
	数据范围： ( -1 * 10^(38 - S), 1 * 10^(38 - S) )
	Decimal256(S)
	数据范围：( -1 * 10^(76 - S), 1 * 10^(76 - S) )
其中：P代表精度，决定总位数（整数部分+小数部分），取值范围是1～76
S代表规模，决定小数位数，取值范围是0～P
根据P的范围，可以有如下的等同写法：

	[ 1 : 9 ]	Decimal(9,2)	Decimal32(2)
	[ 10 : 18 ]	Decimal(18,2)	Decimal64(2)
	[ 19 : 38 ]	Decimal(38,2)	Decimal128(2)
	[ 39 : 76 ]	Decimal(76,2)	Decimal256(2)
注意点：不同精度的数据进行四则运算时，精度(总位数)和规模(小数点位数)会发生变化，具体规则如下：
精度对应的规则

	Decimal64(S1) 运算符 Decimal32(S2) -> Decimal64(S)
	Decimal128(S1) 运算符 Decimal32(S2) -> Decimal128(S）
	Decimal128(S1) 运算符 Decimal64(S2) -> Decimal128(S)
	Decimal256(S1) 运算符 Decimal<32|64|128>(S2) -> Decimal256(S)
可以看出：两个不同精度的数据进行四则运算时，结果数据以最大精度为准
规模(小数点位数)对应的规则
加法|减法：S = max(S1, S2)，即以两个数据中小数点位数最多的为准
乘法： S = S1 + S2(注意：S1精度 >= S2精度)，即以两个数据的小数位相加为准
除法： S = S1，即被除数的小数位为准

#### 2.1.2 字符串类型
**2.1.2.1 String**
字符串可以是任意长度的。它可以包含任意的字节集，包含空字节。因此，字符串类型可以代替其他 DBMSs 中的VARCHAR、BLOB、CLOB 等类型。

**2.1.2.2 FixedString**
	
固定长度的N字节字符串，一般在在一些明确字符串长度的场景下使用，声明方式如下：

	<column_name> FixedString(N)
	-- N表示字符串的长度
注意：FixedString使用null字节填充末尾字符。

#### 2.1.3 日期类型
时间类型分为DateTime、DateTime64和Date三类。需要注意的是目前没有时间戳类型，也就是说，时间类型最高的精度是秒，所以如果需要处理毫秒、微秒精度的时间，则只能借助UInt类型实现。

	Date 类型
用两个字节存储，表示从 1970-01-01 (无符号) 到当前的日期值。日期中没有存储时区信息。

	DateTime 类型
用四个字节（无符号的）存储 Unix 时间戳，允许存储与日期类型相同的范围内的值，最小值为 0000-00-00 00:00:00。时间戳类型值精确到秒（没有闰秒），时区使用启动客户端或服务器时的系统时区。

#### 2.1.4 布尔类型
当前版本没有单独的类型来存储布尔值。可以使用UInt8 类型，取值限制为0或 1。

#### 2.1.5 数组类型
Array(T)，由 T 类型元素组成的数组。T 可以是任意类型，包含数组类型。但不推荐使用多维数组，目前对多维数组的支持有限。

    sql("SELECT array(1, 2) AS x, toTypeName(x)").show()	
    或者
    sql("SELECT [1, 2] AS x, toTypeName(x)").show()
    -- 结果输出
    x      toTypeName(array(1, 2))
    -----  -------------------------
    [1,2]  Array(UInt8)


需要注意的是，数组元素中如果存在Null值，则元素类型将变为Nullable。

    sql("SELECT array(1, 2, NULL) AS x, toTypeName(x)").show()
    -- 结果输出
    x           toTypeName(array(1, 2, NULL))
    ----------  -------------------------------
    [1,2,NULL]  Array(Nullable(UInt8))

另外，数组类型里面的元素必须具有相同的数据类型，否则会报异常

    sql("SELECT array(1, 'a')").show()
    -- 报异常
    DB::Exception: There is no supertype for types UInt8, String because some of them are String/FixedString and some of them are not

#### 2.1.6 枚举类型
枚举类型通常在定义常量时使用，当前版本提供了Enum8和Enum16两种枚举类型。

-- 建表

	sql("CREATE TABLE t_enum (x Enum8('hello' = 1, 'world' = 2)) Engine=Memory").show()


-- INSERT数据

    sql("INSERT INTO t_enum VALUES ('hello'), ('world'), ('hello')").show()

-- 如果定义了枚举类型值之后，不能写入其他值的数据

    sql("INSERT INTO t_enum values('a')").show()
    -- 报异常：Unknown element 'a' for type Enum8('hello' = 1, 'world' = 2)

#### 2.1.7 Tuple类型
Tuple(T1, T2, ...)，元组，与Array不同的是，Tuple中每个元素都有单独的类型，不能在表中存储元组（除了内存表）。它们可以用于临时列分组。在查询中，IN表达式和带特定参数的 lambda 函数可以来对临时列进行分组。

    sql("SELECT tuple(1,'a') AS x, toTypeName(x)").show()
   --结果输出
    
    x        toTypeName(tuple(1, 'a'))
    -------  -----------------------------
    (1,'a')  Tuple(UInt8, String)

   -- 建表
    
    sql("CREATE TABLE t_tuple(c1 Tuple(String,Int8))").show()
   -- INSERT数据

    sql("INSERT INTO t_tuple VALUES(('jack',20))").show()
   -- 查询数据
    
    sql("SELECT * FROM t_tuple").show()
   -- 结果输出
    
    c1
    -----------
    ('jack',20)
-- 如果插入数据类型不匹配，会报异常
    
    sql("INSERT INTO t_tuple VALUES(('tom','xxx'))").show()
    Code: 6. DB::Exception: Cannot parse string 'xxx' as Int8:

#### 2.1.8 特殊数据类型
Nullable
Nullable类型表示某个基础数据类型可以是Null值。其具体用法如下所示：

-- 建表

    sql("CREATE TABLE t_null(x Int8, y Nullable(Int8)) engine=Memory").show()

-- 写入数据

    sql("INSERT INTO t_null VALUES (1, NULL), (2, 3)").show()
    sql("SELECT x + y FROM t_null").show()

-- 结果

    plus(x, y)
    -------------
    NULL
    5


### 2.2 建表

建表有如下几种方式：
#### 方式1

	CREATE TABLE [IF NOT EXISTS] [db.]table_name 
	(
		name1 [type1] [DEFAULT|MATERIALIZED|ALIAS expr1],
		name2 [type2] [DEFAULT|MATERIALIZED|ALIAS expr2],
		...
	) ENGINE = engine
	
示例:

	from dae import sql
	sql("create table if not exists test (user String,age Int32,fees Float32) Engine=MergeTree() order by tuple()")
	

#### 方式2

	CREATE TABLE [IF NOT EXISTS] [db.]table_name AS [db2.]name2 [ENGINE = engine]
	
示例:

	from dae import sql
	sql("create database db2")
	sql("create table if not exists db2.test as default.test Engine=MergeTree() order by tuple() ")
	

#### 方式3

	CREATE TABLE [IF NOT EXISTS] [db.]table_name ENGINE = engine AS SELECT ...

示例:

	from dae import sql
	sql("create table if not exists test2 ENGINE=MergeTree() order by tuple() as select * from test")


其中ENGINE一般指定为MergeTree()，并且还需要指定排序键，例如：

	ENGINE=MergeTree() order by (name1 [,name2...])

或

	ENGINE=MergeTree() order by tuple()

注：1.3.2版本之后建表不再需要指定ENGINE和排序键了，默认会按照MergeTree引擎建表。

### 2.3 数据导入

导入数据有如下几种方式：
#### 方式1

	INSERT INTO [db.]table [(c1, c2, c3)] VALUES (v11, v12, v13), ...
示例:

	from dae import sql
	sql("insert into table test values ('Jack', 32, 23567)")

#### 方式2

	INSERT INTO [db.]table [(c1, c2, c3)] SELECT ...

示例:

	from dae import sql
	sql("insert into table test2 select * from test")

#### 方式3

	INSERT INTO [db.]table from infile 'path/filename' Format [CSV|Parquet]
	
示例:
	
	from dae import sql
	sql("insert into table test from infile './test.csv' format CSV")


### 2.4 数据查询
表建好并导入数据之后便可以对表中的数据进行各种查询了，查询语句的一般形式为：

	SELECT [DISTINCT] expr_list
	    [FROM [db.]table | (subquery) | table_function] [FINAL]
	    [SAMPLE sample_coeff]
	    [ARRAY JOIN ...]
	    [GLOBAL] ANY|ALL INNER|LEFT JOIN (subquery)|table USING columns_list
	    [PREWHERE expr]
	    [WHERE expr]
	    [GROUP BY expr_list] [WITH TOTALS]
	    [HAVING expr]
	    [ORDER BY expr_list]
	    [LIMIT [n, ]m]
	    [UNION ALL ...]
	    [INTO OUTFILE filename]
	    [FORMAT format]
	    [LIMIT n BY columns]

示例:

#### 从数据表查询

    from dae import sql
    sql("select * from test").show()

#### 从外部文件查询

	from dae import sql
	sql("select * from file('./test.csv','CSV','name String, age Int32, fees Float32')").show()

#### 查询子句
**DISTINCT**
	查询结果集在指定字段上只保留一行

**GROUP BY**
   GROUP BY 子句将 SELECT 查询结果转换为聚合模式，目前支持的聚合函数如下：

   sum–对指定字段进行求和，只能对数值型字段求和
   min–求指定字段在查询结果集中的最小值
   max–求指定字段在查询结果集中的最大值


**HAVING**
  允许过滤由 GROUP BY 生成的聚合结果. 它类似于 WHERE ，但不同的是 WHERE 在聚合之前执行，而 HAVING 在之后进行。

**INTO OUTFILE**
  SELECT query 将其输出重定向到本机上的指定文件。

**JOIN**
  连接两个表
  支持的联接类型 
  所有标准 SQL JOIN 支持类型:

	INNER JOIN，只返回匹配的行。
	LEFT OUTER JOIN，除了匹配的行之外，还返回左表中的非匹配行。
	RIGHT OUTER JOIN，除了匹配的行之外，还返回右表中的非匹配行。
	FULL OUTER JOIN，除了匹配的行之外，还会返回两个表中的非匹配行。
	CROSS JOIN，产生整个表的笛卡尔积, “join keys” 是 不 指定。
	JOIN 没有指定类型暗指 INNER. 关键字 OUTER 可以安全地省略。

**LIMIT**
	LIMIT m 允许选择结果中起始的 m 行。

**ORDER BY**
	ORDER BY 子句包含一个表达式列表，每个表达式都可以用 DESC （降序）或 ASC （升序）修饰符确定排序方向。 如果未指定方向, 默认是 ASC。

**SAMPLE**
	SAMPLE K
	这里 k 从0到1的数字（支持小数和小数表示法）。 例如, SAMPLE 1/2 或 SAMPLE 0.5。这里k实际是百分比。

示例：

    SELECT
    Title,
    count() * 10 AS PageViews
    FROM hits_distributed
    SAMPLE 0.1
    WHERE
    CounterID = 34
    GROUP BY Title
    ORDER BY PageViews DESC LIMIT 1000

**SAMPLE N**
这里 n 是足够大的整数。 例如, SAMPLE 10000000.

在这种情况下，查询在至少 n 行（但不超过这个）上执行采样。 例如, SAMPLE 10000000 在至少10,000,000行上执行采样。

**UNION ALL**
联合两个子查询的结果

示例：

    SELECT CounterID, 1 AS table, toInt64(count()) AS c
    FROM test.hits
    GROUP BY CounterID
    UNION ALL
    SELECT CounterID, 2 AS table, sum(Sign) AS c
    FROM test.visits
    GROUP BY CounterID
    HAVING c > 0

**WHERE**
指定条件对查询结果集进行过滤，支持OR，AND等条件组合。

**FROM INFILE**
将外部文件数据导入到本地表中

### 2.5 数据导出

#### 2.5.1 直接展示
示例：

    from dae import sql
    query_sql = 'select * from test_table'
    sql(query_sql).show()

默认打印前100行

#### 2.5.2 导出到文件
示例：

    query_sql = "select * from test_table into outfile './temp.csv'  Format CSV"
    sql(query_sql).show()

保存为csv文件

----------
## 3. SQLTable 与 DataFrame 互转

### 3.1 SQLTable 转换为 DAE Dataframe

    from dae import sql 
    df = sql('select * from test_table').to_df()

查询结果被转换成了dataframe，然后可以直接对dataframe执行相关操作，比如：
	
    print(df.shape)
    print(df)

### 3.2 SQLTable 转换为Pandas Dataframe

	from dae import sql
	pdf=sql('select * from test_table').to_pandas()

查询结果被转换成了Pandas dataframe，然后可以直接对pdf执行Pandas的相关操作，比如：

    pdf.info()

### 3.3  DAE Dataframe 转换为 SQLTable

    from dae import sql
	import pandas as pd
	data = [['Google',22],['baidu',20],['Wiki',13]]
	df = pd.DataFrame(data,columns=['Site','Age'], dtype=float)
	ds = sql('select *FROM {df}').show()

可以用sql语句直接查询df。


​	
## 4.  Cache
### 4.1 Cache的作用
cache模块旨在通过缓存方式提升离线分析的性能，解决以下问题：
* 重复查询：在很多离线分析场景下，用户会消耗额外的时间和资源用于同一sql语句的重复查询。通过cache可快速复用之前查询的结果。
* 断点续跑：复杂查询，可能在后期故障退出，之前完成的大量计算需要重复执行。通过cache可以做阶段性的checkpoint，方便断点续跑。
* 远程数据缓存至本地：在很多离线分析场景下，数据可能是在远程存储上，频繁从远程拉取数据成本高。通过cache可将数据缓存至本地，提升离线分析性能。
* 同时，cache模块也支持对python函数的缓存

### 4.2 sql节点的cache操作

    from dae import sql, cache, uncache
    
    t1 = sql('SELECT * FROM table1')
    t2 = sql('SELECT * FROM table2')
    
    # 缓存t1、t2节点
    t1.cache()
    t2.cache()
    
    # 后续sql的操作，在使用t1、t2节点时，会复用对应节点的缓存
    t3 = sql('SELECT * from {t1} join on {t2}')
    t3.show()
    
    # cache的管理：支持LRU策略下的自动cache清除，同时也支持手动清除所有cache
    uncache() # 手动清除所有cache的操作

### 4.3 函数节点的cache操作

    from dae import sql
    import time
    
    # 使用cache()装饰器，可以使任意python函数具备cache能力
    @cache()
    def expensive_cal(x, y):
        time.sleep(5)
        return x + y
    
    #首次运行expensive_cal函数，耗时5s+，同时结果被缓存
    expensive_cal(1, 1)
    
    # 再次运行expensive_val函数，直接返回缓存结果，耗时在毫秒级
    expensive_cal(1, 1)
    
    # 改变入参，重新运行expensive_cal，cache miss，耗时5s+，同时结果再次被缓存
    expensive_cal(1, 2)
    
    # 说明：当函数的入参、函数体、函数依赖的外部变量以及函数依赖的外部函数，任意一项发生变化时，则函数cahce会miss，并重新缓存，以保证函数结果的准确。

## 5. 外部数据对接
### 5.1 DAE数据对接 
本节只针对安装了DAE集群组件的用户，DAE单机用户请忽略。
DAE集群的数据，可以认为是一种特殊形式的catalog，catalog内置在DAE中。使用方式如下：


    sql("show catalogs").show()
    _ _ _ _ _
    dae
    
    sql("show databases from dae").show()
    _ _ _ _ _
    db1
    db2
    
    sql("create database my_db1 from dae.db1").show()
    _ _ _ _ _
    create my_db1 success
    
    #接下来，可以访问本地的my_db1中的table数据: *
    sql("select * from my_db1.table1").show()
    
    #除了直接sql分析，也可以将数据“取数”到Pandas Dataframe或DAE Dataframe：
    df = sql("select * from my_db1.table1").to_pandas()
    df = sql("select * from my_db1.table1").to_df()
    
    #然后可以按python dataframe方式做计算
    df = df[df.col1 > 4]     
    
    *说明：除了create database 也可以单独创建一张表：sql("create table my_tb1 from dae.db1.table1").show()

### 5.2 Iceberg对接
#### 5.2.1 iceberg-catalog支持
	可以通过catalog支持iceberg库、表的建立
#### 5.2.2 使用方式
   spark iceberg原生表：

    CREATE TABLE local.db.sc1 (
        id bigint,
        data string,
        category string)
    USING iceberg;

DAE 对应的表建立语句：

	sql("CREATE TABLE icsc1 (id Int64,data String, category String) ENGINE=Iceberg('hdfs://localhost:8020/user/hive/warehouse/', 'Parquet','db','sc1','HADOOP')")

其中Iceberg中有五个参数
	param1：如果是FE模式，参数1代表 fe_ip:fe_rpc_port；如果是HADOOP模式，参数1代表warehouse url
	param2：存储文件格式
	param3：iceberg原生db名
	param4：iceberg原生table名
	param5：type，分为FE/HADOOP，其中FE是支持DAE、HADOOP为spark-hadoop模式表

#### 5.2.3 嵌套格式支持
目前支持iceberg的nested，map，array以及他们的组合格式，例子如下所示：
iceberg表1：

		CREATE TABLE local.db.s2 (
		    id bigint,
		    data string,
		    category string,
		    point struct<x:bigint,y:bigint>)
		USING iceberg;

DAE表1：

		CREATE TABLE ics2 (
			id Int64, 
			data String, 
			category String, 
			point Tuple(x Int64, y Int64)) 
		ENGINE=Iceberg('hdfs://localhost:8020/user/hive/warehouse/', 'Parquet','db','s2','HADOOP')

支持复杂格式内部单一格式的非空，复杂格式本身非空不支持
	
iceberg表2：（map->Map)

	CREATE TABLE local.db.s3 (
	    id bigint,
	    data string,
	    category string,
	    point map<bigint,bigint>)
	USING iceberg;

DAE表2：
	
	CREATE TABLE ics3 (
		id Int64, 
		data String,
		category String, 
		point Map(Int64, Int64)) 
	ENGINE=Iceberg('hdfs://localhost:8020/user/hive/warehouse/', 'Parquet','db','s3','HADOOP')

iceberg表3：（array->Array)

	CREATE TABLE local.db.s4 (
	    id bigint,
	    data string,
	    category string,
	    point array<bigint>)
	USING iceberg;
	
	CREATE TABLE ics4 (
		id Int64, 
		data String, 
		category String, 
		point Array(Int64)) 
	ENGINE=Iceberg('hdfs://localhost:8020/user/hive/warehouse/', 'Parquet','db','s4','HADOOP')

#### 5.2.4 查询优化相关
1.3.2版本会支持部分辅助数据下推

### 5.3 HIVE对接
DAE初步支持读取HIVE表数据

    sql("CREATE TABLE dae_hive_talbe (foo UInt32,bar String,city String) ENGINE=HIVE('hive-server:10003','test','hive_table1','CSV') partition by city;

    HIVE中的参数含义为
        参数1：hivemetastore url,
        参数2：hive的db名
        参数3：hive的table名
        参数4：存储文件的格式，支持CSV/Parquet
        支持分区表文件

    HIVE外表schema需要和hive表本身schema一致；
### 5.4 HDFS对接
DAE支持读取写入HDFS外部表

    sql("CREATE TABLE hdfs_engine_table (name String, value UInt32) ENGINE=HDFS('hdfs://hdfs1:9000/other_storage', 'CSV')")

    HDFS中参数含义为
        参数1：hdfs中文件夹的地址
        参数2：文件类型,支持 CSV/Parquet

    读取、插入数据例子
    sql("INSERT INTO hdfs_engine_table VALUES ('one', 1), ('two', 2), ('three', 3)")
    sql("SELECT * FROM hdfs_engine_table LIMIT 2").show()


### 5.5 MYSQL对接
    
    sql("CREATE TABLE dae_mysql_talbe (foo UInt32, bar String,city String) ENGINE=MySQL('host:port', 'database', 'table', 'user', 'password'[, replace_query, 'on_duplicate_clause'])")
    ​参数含义为
        参数1：host:port — MySQL 服务器地址。
        参数2：database — 数据库的名称。
        参数3：table — 表名称。
        参数4：user — 数据库用户。
        参数5：password — 用户密码。
        参数6：replace_query — 将 INSERT INTO 查询是否替换为 REPLACE INTO 的标志。如果 replace_query=1，则替换查询
        参数7：'on_duplicate_clause' — 将 ON DUPLICATE KEY UPDATE 'on_duplicate_clause' 表达式添加到 INSERT 查询语句中。例如：impression = VALUES(impression) + impression。如果需要指定 'on_duplicate_clause'，则需要设置 replace_query=0。如果同时设置 replace_query = 1 和 'on_duplicate_clause'，则会抛出异常。

    此时，简单的 WHERE 子句（例如 =, !=, >, >=, <, <=）是在 MySQL 服务器上执行。
    其余条件以及 LIMIT 采样约束语句仅在对MySQL的查询完成后才在DAE中执行。
    MySQL 引擎不支持 可为空 数据类型，因此，当从MySQL表中读取数据时，NULL 将转换为指定列类型的默认值（通常为0或空字符串）。

    与此同时，DAE也支持MYSQL库引擎，如下所示
    sql("CREATE DATABASE [IF NOT EXISTS] db_name [ON CLUSTER cluster] ENGINE = MySQL('host:port', ['database' | database], 'user', 'password')")


### 5.6 MongoDB对接
MongoDB 外表引擎是只读表引擎，允许从远程 MongoDB 集合中读取数据(SELECT查询)。引擎只支持非嵌套的数据类型。不支持 INSERT 查询。

    sql("CREATE TABLE [IF NOT EXISTS] [db.]table_name(name1 [type1],name2 [type2]) ENGINE = MongoDB(host:port, database, collection, user, password)")

    ​参数含义为
        参数1：host:port — MongoDB 服务器地址.
        参数2：database — 数据库名称.
        参数3：collection — 集合名称.
        参数4：user — MongoDB 用户.
        参数5：password — 用户密码.

### 5.7 S3对接
    sql("CREATE TABLE s3_engine_table (name String, value UInt32) ENGINE = S3(path, [aws_access_key_id, aws_secret_access_key,] format, [compression])")
    ​参数含义为
        参数1：path — 带有文件路径的 Bucket url。在只读模式下支持以下通配符: *, ?, {abc,def} 和 {N..M} 其中 N, M 是数字, 'abc', 'def' 是字符串. 更多信息见下文.
        参数2：format — 文件的格式.
        参数3：aws_access_key_id, aws_secret_access_key - AWS 账号的长期凭证. 你可以使用凭证来对你的请求进行认证.参数是可选的. 如果没有指定凭据, 将从配置文件中读取凭据. 更多信息参见 使用 S3 来存储数据.
        参数4：compression — 压缩类型. 支持的值: none, gzip/gz, brotli/br, xz/LZMA, zstd/zst. 参数是可选的. 默认情况下，通过文件扩展名自动检测压缩类型.

    读取、插入数据例子
    INSERT INTO s3_engine_table VALUES ('one', 1), ('two', 2), ('three', 3);
    SELECT * FROM s3_engine_table LIMIT 2;

### 5.8 Kafka对接
    sql("CREATE TABLE kafka_engine_table (name String, value UInt32) ENGINE = Kafka(kafka_broker_list, kafka_topic_list, kafka_group_name, kafka_format[, kafka_row_delimiter, kafka_schema, kafka_num_consumers])")

    必要参数：
        kafka_broker_list – 以逗号分隔的 brokers 列表 (localhost:9092)。
        kafka_topic_list – topic 列表 (my_topic)。
        kafka_group_name – Kafka 消费组名称 (group1)。如果不希望消息在集群中重复，请在每个分片中使用相同的组名。
        kafka_format – 消息体格式。使用与 SQL 部分的 FORMAT 函数相同表示方法，例如 JSONEachRow。了解详细信息，请参考 Formats 部分。

    可选参数：
        kafka_row_delimiter - 每个消息体（记录）之间的分隔符。
        kafka_schema – 如果解析格式需要一个 schema 时，此参数必填。例如，普罗托船长 需要 schema 文件路径以及根对象 schema.capnp:Message 的名字。
        kafka_num_consumers – 单个表的消费者数量。默认值是：1，如果一个消费者的吞吐量不足，则指定更多的消费者。消费者的总数不应该超过 topic 中分区的数量，因为每个分区只能分配一个消费者。

### 5.9 PostgreSQL对接
PostgreSQL 引擎允许 DAE 对存储在远程 PostgreSQL 服务器上的数据执行 SELECT 和 INSERT 查询.

    sql("CREATE TABLE [IF NOT EXISTS] [db.]table_name [ON CLUSTER cluster](name1 [type1] [DEFAULT|MATERIALIZED|ALIAS expr1] [TTL expr1]) ENGINE = PostgreSQL('host:port', 'database', 'table', 'user', 'password'[, `schema`])")

    ​参数含义为
        host:port — PostgreSQL 服务器地址.
        database — 数据库名称.
        table — 表名称.
        user — PostgreSQL 用户.
        password — 用户密码.
        schema — Non-default table schema. 可选.

    创建、select 例子
    sql("CREATE TABLE default.postgresql_table(`float_nullable` Nullable(Float32),`str` String,`int_id` Int32) ENGINE = PostgreSQL('localhost:5432', 'public', 'test', 'postges_user', 'postgres_password')")
    sql("SELECT * FROM postgresql_table WHERE str IN ('test')").show()

    与此同时，DAE也支持PostgreSQL库引擎，如下所示
    sql("CREATE DATABASE test_database ENGINE = PostgreSQL('host:port', 'database', 'user', 'password'[, `use_table_cache`]);")
        use_table_cache — 定义数据库表结构是否已缓存或不进行。可选的。默认值： 0.

### 5.10 EmbeddedRocksDB对接
    
    sql("CREATE TABLE [IF NOT EXISTS] [db.]table_name [ON CLUSTER cluster](name1 [type1] [DEFAULT|MATERIALIZED|ALIAS expr1]) ENGINE = EmbeddedRocksDB PRIMARY KEY(primary_key_name)")

    必要参数:
        primary_key_name – any column name in the column list.
        必须指定 primary key, 仅支持主键中的一个列. 主键将被序列化为二进制的rocksdb key.
        主键以外的列将以相应的顺序在二进制中序列化为rocksdb值.
        带有键 equals 或 in 过滤的查询将被优化为从 rocksdb 进行多键查询.

    例子
    sql("CREATE TABLE test(`key` String,`v1` UInt32) ENGINE = EmbeddedRocksDBPRIMARY KEY key")

### 5.11 Catalog管理外部数据
#### 5.11.1 Catalog的定义
Catalog功能，一般需要运维人员参与，普通用户可以忽略。如果运维人员已完成了catalog配置，用户可跳到第3、4小节查看使用方法。
待分析的数据，可能分布在HIVE、HDFS、MySQL、BOS等不同的系统中（如上述章节所属）。Catalog功能，可帮用户集中管理外部数据源：管理用户可用的数据库和表的目录结构，给用户一个全局的数据视图，在引入外部数据和联邦查询中有重要作用。
Catalog功能有三个功能：可以解耦数据提供方和使用方；可以简化数据使用流程；可以避免直接配置密码、避免安全问题。
Catalog表示一个数据来源，可以包含来自不同系统的数据库和表，比如customer_catalog表示分析用户购买行为相关的数据源，其中包含来自MySQL的order_db和HIVE的customer_history_info_db等，通过联合分析MySQL order_db.order_list和HIVE customer_history_info_db.show_list来分析用户的喜好。所有分析师，只需要**配置Catalog源**的信息（比如http server的访问信息），就能看到这些数据库和表，就可以：**展示Catalog包含的Databases和Tables**，**从Catalog源导入某Database或Table** 到DAE里做分析。
        
#### 5.11.2 配置Catalog源
本步骤一般由运维人员完成。
Catalog源的配置文件，是dae的运行目录下的.jarvis/catalog_conf.json文件。首次启动，会产生空文件。用户可以编辑它，配置自己的Catalog源(注意：目前只重点支持了http类型）。

.jarvis/catalog_conf.json内容：
     
    [
        {
            "type": "http",
            "name": "http_catalog",
            "uri": "http://ip:8080/http_catalog/",
            "user": "user",
            "password": "nginx_password_base64"
        }
    ]

说明：
1， uri填：nginx服务的ip/port和catalog所在的nginx路径
2， user和password填： nginx的账号和 密码的base64。
3， Catalog源提前放置到Nginx服务的指定目录下（如/http_catalog)，文件组织成如下结构： (tree http_catalog的结果）

    http_catalog
    ├── mysql_db
    │   ├── conn_info.json
    │   ├── table1
    └── postgresql_db
        ├── conn_info.json
        ├── table2
        └── table3

其中http_catalog/mysql_db/table1 内容如下:   （列名和类型\t分隔）

    col1 \t Int32,
    col2 \t String

   
其中http_catalog/mysql_db/conn_info.json  内容如下: （password需要base64编码）
```json
{
    "type": "MySQL",  #database类型，可以为BOS/HIVE/Iceberg/MySQL/..
    "host_port": "host:port",  #MySQL的服务host,post
    "user": "mysql_user",  
    "password": "mysql_password_base64_encode",
    "format": {
         "table1": "CSV"  #CSV/Parquet等格式
    }
}
```
#### 5.11.3 展示Catalog包含的Databases和Tables
catalog在database上一级，SHOW命令：
```python
sql("SHOW DATABASES FROM http_catalog") 
sql("SHOW TABLES FROM http_catalog.db1") 
sql("DESC http_catalog.db1.table1") 
```
#### 5.11.4 从Catalog源导入Database或Table
```python
sql("CREATE DATABASE mydb1 FROM http_catalog.db1")
sql("CREATE TABLE mytable1 FROM http_catalog.db1.table1')")
```
导入后，可以按本地库或表一样访问外部数据： （但数据仍然在远端数据源，可结合cache把远端数据源缓存在本地、来加快查询速度）
```python	
sql("SHOW TABLES FROM mydb1")
sql("SELECT * FROM mytable1")
sql("DROP mydb1")
```
****
