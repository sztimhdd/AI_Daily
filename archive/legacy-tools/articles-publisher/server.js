const express = require('express');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

/**
 * 🛡️ 终极私有发布 API - V4.0 稳定版
 * 功能：处理云端 n8n 请求，唤醒本地浏览器插件，绕过 MCP 冲突，全自动分发至知乎与微信。
 */

const app = express();
app.use(express.json({ limit: '50mb' })); // 支持超长图文

// ⚠️ 配置区
const SECRET_TOKEN = process.env.PUBLISH_API_TOKEN;
const WECHAT_TOKEN = process.env.WECHATSYNC_TOKEN;
const PORT = 8888;

app.post('/api/publish', (req, res) => {
    // 1. 密钥安全拦截
    const authHeader = req.headers.authorization;
    if (authHeader !== `Bearer ${SECRET_TOKEN}`) {
        console.log(`[${new Date().toLocaleTimeString()}] 🚫 拦截到非法请求，密钥错误。`);
        return res.status(401).json({ error: 'Unauthorized' });
    }

    const { title, content, platforms } = req.body;
    if (!content) return res.status(400).json({ error: 'Missing content' });

    console.log(`\n[${new Date().toLocaleTimeString()}] 📥 收到云端任务: ${title || '无标题'}`);

    // 2. 预处理：生成安全的文件名并存为本地临时 MD
    const safeTitle = (title || `draft_${Date.now()}`).replace(/[\\/:*?"<>|]/g, "").trim();
    const tempFilePath = path.join(__dirname, `${safeTitle}.md`);
    fs.writeFileSync(tempFilePath, content, 'utf8');

    // 3. 预处理：强制清理平台字符串中的空格，防止 CLI 解析失败
    const targetPlatforms = (platforms || 'zhihu,weixin').replace(/\s+/g, '');
    console.log(`🚀 准备唤醒浏览器推送到: ${targetPlatforms}...`);

    // 4. 🌟 核心环境净化：彻底抹除 Claude/MCP 等干扰变量
    const cleanEnv = { ...process.env };

    // 强制切断与一切 AI/MCP 守护进程的关联，防止同步微信时截胡
    delete cleanEnv.NODE_OPTIONS;
    delete cleanEnv.MCP_SERVER_URL;
    delete cleanEnv.CLAUDE_TOKEN;
    delete cleanEnv.ELECTRON_RUN_AS_NODE;

    // 注入合法插件通信 Token
    cleanEnv.WECHATSYNC_TOKEN = WECHAT_TOKEN;

    // 5. 构建底层命令
    const command = `wechatsync sync "${tempFilePath}" --title "${title}" -p ${targetPlatforms}`;

    const execOptions = {
        timeout: 120000,       // 微信涉及图片上传，放宽到 120 秒
        windowsHide: true,     // 执行时隐藏 CMD 窗口
        env: cleanEnv          // 使用净化后的环境
    };

    console.log(`⚙️ 执行指令: wechatsync sync...`);

    // 6. 执行发布动作
    exec(command, execOptions, (error, stdout, stderr) => {
        // 及时清理本地临时文件
        if (fs.existsSync(tempFilePath)) {
            try { fs.unlinkSync(tempFilePath); } catch(e) {}
        }

        // 打印底层执行日志，方便调试
        if (stdout) console.log(`[CLI 标准输出]:\n${stdout}`);
        if (stderr) console.log(`[CLI 警告/过程]:\n${stderr}`);

        if (error) {
            console.error(`❌ Wechatsync 执行失败: ${error.message}`);
            // 如果是因为 MCP 报错，在这里可以捕捉到
            return res.status(500).json({
                status: 'error',
                message: error.message,
                details: stderr
            });
        }

        console.log(`✅ [${title}] 分发成功！草稿已安全存入后台。`);
        res.status(200).json({
            status: 'success',
            message: '指令已成功执行，草稿已推送到浏览器'
        });
    });
});

app.listen(PORT, () => {
    console.log(`🛡️ 终极私有发布 API V4.0 已就绪`);
    console.log(`📍 监听端口: ${PORT}`);
    console.log(`🔑 注入 Token: ${WECHAT_TOKEN.substring(0,8)}...`);
    console.log(`------------------------------------------`);
});
