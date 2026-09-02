-- ============================================================
-- PaperForge V2 数据库建表脚本
-- 数据库: paperforge
-- 字符集: utf8mb4
-- ============================================================

-- 1. 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS `paperforge` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `paperforge`;

SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- 2. 论文主表
-- ============================================================
DROP TABLE IF EXISTS `template_configs`;
DROP TABLE IF EXISTS `chapters`;
DROP TABLE IF EXISTS `designs`;
DROP TABLE IF EXISTS `papers`;

CREATE TABLE `papers` (
    `id` VARCHAR(32) NOT NULL COMMENT '论文ID',
    `title` VARCHAR(200) NOT NULL COMMENT '论文题目',
    `techs` JSON NOT NULL COMMENT '技术栈列表',
    `word_level` VARCHAR(20) DEFAULT 'medium' COMMENT '字数档位: small/medium/large',
    `style` VARCHAR(50) DEFAULT '严谨学术' COMMENT '写作风格',
    `requirements` TEXT NULL COMMENT '用户补充需求',
    `status` VARCHAR(20) DEFAULT 'draft' COMMENT '状态: draft/generating/done/updating',
    `mode` VARCHAR(20) DEFAULT 'template' COMMENT '生成模式: template/ai',
    `word_count` INT DEFAULT 0 COMMENT '总字数',
    `chapter_count` INT DEFAULT 0 COMMENT '章节数',
    `chart_count` INT DEFAULT 0 COMMENT '图表数',
    `generated_at` DATETIME NULL COMMENT '生成时间',
    `updated_at` DATETIME NULL COMMENT '更新时间',
    `note` TEXT NULL COMMENT '备注信息',
    `user_id` VARCHAR(32) NULL COMMENT '用户ID（预留）',
    `design_id` VARCHAR(32) NULL COMMENT '当前激活系统设定ID',
    PRIMARY KEY (`id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '论文主表';

-- ============================================================
-- 3. 章节表
-- ============================================================
CREATE TABLE `chapters` (
    `id` VARCHAR(32) NOT NULL COMMENT '章节ID',
    `paper_id` VARCHAR(32) NOT NULL COMMENT '所属论文ID',
    `key` VARCHAR(20) NOT NULL COMMENT '章节Key: summary/ch1/ch2...',
    `seq` INT NOT NULL DEFAULT 0 COMMENT '显示顺序',
    `title` VARCHAR(100) NOT NULL COMMENT '章节标题（用户可修改）',
    `hint` VARCHAR(200) NULL COMMENT '写作要求提示',
    `content_md` TEXT NULL COMMENT 'Markdown内容',
    `content_html` TEXT NULL COMMENT 'HTML内容（渲染备用）',
    `status` VARCHAR(20) DEFAULT 'generated' COMMENT '状态: pending/generating/generated/updated',
    `is_custom` TINYINT(1) DEFAULT 0 COMMENT '是否为用户自定义章节',
    `is_enabled` TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    `version` INT DEFAULT 1 COMMENT '版本号',
    `design_version` INT DEFAULT 1 COMMENT '关联的系统设定版本',
    `generated_at` DATETIME NULL COMMENT '生成时间',
    `updated_at` DATETIME NULL COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_chapters_paper_id` (`paper_id`),
    INDEX `idx_chapters_key` (`key`),
    INDEX `idx_chapters_enabled` (`is_enabled`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '章节表';

-- ============================================================
-- 4. 系统设定表（保证全篇一致性）
-- ============================================================
CREATE TABLE `designs` (
    `id` VARCHAR(32) NOT NULL COMMENT '设定ID',
    `paper_id` VARCHAR(32) NULL COMMENT '所属论文ID',
    `modules` JSON NOT NULL COMMENT '模块列表: [{"name":"用户管理","desc":"..."}]',
    `roles` JSON NOT NULL COMMENT '角色列表: ["管理员","普通用户"]',
    `tables` JSON NOT NULL COMMENT '数据表列表: [{"name":"sys_user","title":"用户信息表","desc":"..."}]',
    `features` JSON NOT NULL COMMENT '功能列表: [{"module":"用户管理","desc":"..."}]',
    `domain_note` VARCHAR(200) NULL COMMENT '领域说明',
    `version` INT DEFAULT 1 COMMENT '版本号',
    `is_latest` TINYINT(1) DEFAULT 1 COMMENT '是否最新版本',
    `created_at` DATETIME NULL COMMENT '创建时间',
    `updated_at` DATETIME NULL COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_designs_paper_id` (`paper_id`),
    INDEX `idx_designs_latest` (`is_latest`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '系统设定表';

-- ============================================================
-- 5. 模板配置表（可配置化）
-- ============================================================
CREATE TABLE `template_configs` (
    `id` VARCHAR(32) NOT NULL COMMENT '配置ID',
    `user_id` VARCHAR(32) NULL COMMENT '用户ID（空为系统默认）',
    `name` VARCHAR(50) NOT NULL DEFAULT '默认模板' COMMENT '模板名称',
    `is_default` TINYINT(1) DEFAULT 0 COMMENT '是否为系统默认模板',
    `chapter_order` JSON NOT NULL COMMENT '章节顺序与标题配置: [{"key":"summary","title":"摘要与关键词","enabled":true}]',
    `custom_chapters` JSON NOT NULL COMMENT '用户自定义章节列表',
    `available_chapters` JSON NOT NULL COMMENT '系统预定义章节池',
    `description` VARCHAR(200) NULL COMMENT '模板描述',
    `version` INT DEFAULT 1 COMMENT '配置版本',
    `created_at` DATETIME NULL COMMENT '创建时间',
    `updated_at` DATETIME NULL COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_template_user_id` (`user_id`),
    INDEX `idx_template_default` (`is_default`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '模板配置表';

ALTER TABLE `chapters`
    ADD CONSTRAINT `fk_chapters_paper_id`
    FOREIGN KEY (`paper_id`) REFERENCES `papers` (`id`) ON DELETE CASCADE;

ALTER TABLE `designs`
    ADD CONSTRAINT `fk_designs_paper_id`
    FOREIGN KEY (`paper_id`) REFERENCES `papers` (`id`) ON DELETE SET NULL;

ALTER TABLE `papers`
    ADD CONSTRAINT `fk_papers_design_id`
    FOREIGN KEY (`design_id`) REFERENCES `designs` (`id`) ON DELETE SET NULL;

SET FOREIGN_KEY_CHECKS = 1;
