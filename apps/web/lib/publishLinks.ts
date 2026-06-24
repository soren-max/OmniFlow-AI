import type { Platform } from "@/types";

export type PublishHandoffStatus =
  | "handoff_ready"
  | "handoff_opened"
  | "manual_publish_required";

export interface PublishHandoffLink {
  platform: Platform;
  officialPublishUrl: string;
  status: PublishHandoffStatus;
}

export const PUBLISH_HANDOFF_LINKS: Record<Platform, PublishHandoffLink> = {
  wechat: {
    platform: "wechat",
    officialPublishUrl: "https://mp.weixin.qq.com/",
    status: "manual_publish_required",
  },
  zhihu: {
    platform: "zhihu",
    officialPublishUrl: "https://www.zhihu.com/creator",
    status: "manual_publish_required",
  },
  bilibili: {
    platform: "bilibili",
    officialPublishUrl: "https://member.bilibili.com/platform/home",
    status: "manual_publish_required",
  },
  xiaohongshu: {
    platform: "xiaohongshu",
    officialPublishUrl: "https://creator.xiaohongshu.com/",
    status: "manual_publish_required",
  },
  douyin: {
    platform: "douyin",
    officialPublishUrl: "https://creator.douyin.com/",
    status: "manual_publish_required",
  },
};

export function getPublishHandoffLink(platform: string): PublishHandoffLink | null {
  if (platform in PUBLISH_HANDOFF_LINKS) {
    return PUBLISH_HANDOFF_LINKS[platform as Platform];
  }
  return null;
}

/** Chinese display labels for handoff status values. */
export const HANDOFF_STATUS_LABELS: Record<string, string> = {
  handoff_ready: "可打开发布页",
  handoff_opened: "已打开",
  manual_publish_required: "需手动提交",
};
