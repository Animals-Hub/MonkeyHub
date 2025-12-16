# Pighub 图片爬取

目标：把 `https://www.pighub.top/all` 页面上通过“加载更多猪猪”懒加载出来的所有图片下载到 `imgs/`。

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## 使用

```bash
python crawl_pighub_images.py --out imgs
```

可选参数：

- `--headful`：打开可视化浏览器（便于观察是否点到了“加载更多猪猪”）
- `--max-rounds 300`：最多滚动/点击轮数
- `--settle-rounds 6`：连续 N 轮没有新增图片且没点到按钮则停止
- `--concurrency 8`：并发下载数

下载结果：

- `imgs/`：图片文件
- `imgs/manifest.jsonl`：已下载 URL 清单（可用于断点续跑）
- `imgs/failed.txt`：失败列表（可重试）

## AI 测试：把 IP 替换成 monkey-ip.png（单张）

前提：根目录放好 `.env`（或设置环境变量），包含：

- `OPENAI_BASE_URL`
- `OPENAI_API_KEY`

可参考：`.env.example`

安装依赖后运行：

```bash
python ai_monkey_ip_one.py --input imgs/000001_1猪_ee8db9bcec69.jpg --out out_test_monkey.png
```

不传 `--input` 会自动选 `imgs/` 里第一张非 GIF 图片。

## AI 批量：处理 imgs/（跳过 GIF）

输出默认到 `imgs_monkey/`，并写入断点清单：

- `imgs_monkey/manifest.jsonl`
- `imgs_monkey/failed.txt`

先小批量试跑：

```bash
python ai_monkey_ip_batch.py --limit 5 --concurrency 2
```

全量跑（可按接口性能调整并发/超时/重试）：

```bash
python ai_monkey_ip_batch.py --concurrency 3 --timeout 900 --retries 2
```

默认会根据 `manifest.jsonl` 自动跳过已经成功处理过的输入；如需强制重跑加 `--no-resume`。
