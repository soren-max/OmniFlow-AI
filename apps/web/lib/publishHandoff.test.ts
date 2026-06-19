import assert from "node:assert/strict";
import test from "node:test";

import { buildManualPublishText, getPreviewTags } from "./publishHandoff.ts";

test("getPreviewTags reads tags from metadata", () => {
  assert.deepEqual(getPreviewTags({ tags: ["ai", "#agent"] }), ["ai", "#agent"]);
});

test("getPreviewTags reads space separated hashtags", () => {
  assert.deepEqual(getPreviewTags({ hashtags: "ai agent contentops" }), ["ai", "agent", "contentops"]);
});

test("buildManualPublishText includes title, body, and tags for copy handoff", () => {
  const copyText = buildManualPublishText({
    title: "AI Agent 如何提升多平台内容运营效率",
    content: "用于手动发布的正文内容。",
    metadata: {
      tags: ["AI", "ContentOps"],
      cta: "欢迎留言交流。",
    },
  });

  assert.match(copyText, /标题：AI Agent 如何提升多平台内容运营效率/);
  assert.match(copyText, /正文：\n用于手动发布的正文内容。/);
  assert.match(copyText, /#AI #ContentOps/);
  assert.match(copyText, /CTA：\n欢迎留言交流。/);
});
