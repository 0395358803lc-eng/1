# Hợp đồng dữ liệu và checkpoint
Tất cả JSON UTF-8; CSV UTF-8 BOM nếu dùng Excel; thời gian giây, không dùng lẫn ms, mỗi file ghi schema_version và job_id nếu khả thi. ID ổn định theo nguồn. File lớn lưu theo batch; manifest ghi phạm vi và hash. Mọi đường dẫn trỏ vào đúng `REVIEW_PHIM_WORKSPACE`. Không ghi credential, device/link/session ID.

## Cấu trúc workspace
```text
<film_dir>/REVIEW_PHIM_WORKSPACE/
  workspace_manifest.json
  imports/<import-id>/migration_report.json
  profiles/channels/
  profiles/servers/
  assets/branding/<channel-id>/
  shared/python/.venv/
  shared/models/
  shared/cache/
  shared/bin/
  jobs/<job-id>/
    config.json
    state.json
    approval_log.json
    logs/
    reports/
    asr/
    frames/
    understanding/
    script/
    tts/
    timeline/
    preview/
    postproduction/
    delivery/
    youtube/
```
Không copy phim nguồn vào workspace theo mặc định; config lưu source path + fingerprint. `workspace_manifest.json` tối thiểu gồm schema_version, workspace_root, created_at, selected_source {path, size_bytes, mtime_ns, sha256 optional}, logo_source {path, selected_file, sha256 optional}, channel_id nếu user đã chọn, jobs và imports. Không lưu deviceId/link_id, email hoặc credential.

## Artefact theo giai đoạn
| Giai đoạn | Tệp gợi ý / cấu trúc tối thiểu |
|---|---|
| Bootstrap | `workspace_manifest.json`, `imports/<import-id>/migration_report.json`, danh mục môi trường và approval log |
| 1 | `jobs/<job-id>/config.json`, `state.json`, `environment_report.json`, `source_probe.json`, `logs/`; source_fingerprint {size_bytes,mtime_ns,sha256 optional} |
| 2 | `asr/transcript_source.json` {language,duration,segments:[{id,start,end,text,words,confidence,flags}]}; `transcript_vi.json` {segments:[{id,start,end,text_source,text_vi,needs_review,source_word_timestamps}]}; TXT/SRT/VTT, report |
| 3 | `frames/index.json` {source_fingerprint,interval_seconds,frames:[{id,requested_seconds,actual_seconds,path}]}; observations batches; `visual_transcript_timeline.json` |
| 4 | `understanding/flagged_ranges.json`, retries/, evidence_sheets/, `film_understanding_verified.md`, verification_report.json |
| 5 | `script/review_script_v1.txt`, `review_script_v2.txt`, audit, sources.json |
| 6 | `tts/segments/part_*.wav`, candidates/, `narration_final.wav`, narration_timeline.json, qc_report.json |
| 7 | `timeline/narration_units.json`, scene_database.json, scene_matching.json, video_timeline_draft.json / CSV |
| 8 | `preview/preview_v1.mp4`, sheets/, visual_cut_review.csv, changes.json, video_timeline_v2.json / CSV, preview_v2.mp4, report |
| 9 | `postproduction/subtitle_cues.json`, narration_vi.srt/.ass, narration_master.wav, music_original.wav, music_ducked.wav, mix.wav, audio_report.json, subtitle_report.json |
| 10 | `delivery/review_final.mp4`, review_final_logo.mp4 nếu áp dụng, render_report.json, final_delivery_report.json, sha256 |
| 11 | `youtube/title.txt`, description.txt, hashtags.txt, thumbnail.png nếu đã tạo, sources.json, delivery_manifest.json |

## Nhập workspace cũ
`migration_report.json` ghi source_workspace, import_id, inspected_at, file_manifest, source/config fingerprint comparisons, imported/skipped/stale artefacts, destination paths, conflicts, reasons và approval reference. Nhập không overwrite; file trùng tên được giữ trong namespace/version riêng. Giữ nguyên workspace cũ. Artefact sai fingerprint chỉ được lưu tham khảo và phải đánh stale.

## Approval log
`approval_log.json` là danh sách sự kiện append-only: {approval_id, scope_type: bootstrap|stage, stage_number optional, scope_description, user_approval_text, approved_at, status, evidence_paths, notes}. Không lưu credentials hoặc ID thiết bị/tài khoản.

## Timeline JSON (cho script check_timeline.py)
```json
{"fps":"25/1","duration":4.0,"source_duration":120.0,"clips":[{"clip_id":1,"unit_id":1,"narration":"Lời kể.","review_start_frame":0,"review_end_frame":100,"source_start":20.0,"source_end":24.0,"speed":1.0,"transition":"cut","visual_observation":"Mô tả ảnh thực","evidence_frame_ids":[5],"flags":[]}]}
```
`fps` có thể là số hoặc phân số string. Frame end exclusive. Nếu speed khác 1, source span/speed phải khớp review duration trong dung sai. Script hỗ trợ hard-cut liên tục; transition overlap cần validate bổ sung. Không lấy output helper làm bằng chứng nội dung khớp.

## State
`workflow_state.py init --state PATH --job-id ID --source-fingerprint FINGERPRINT` tạo 40 bước pending, không overwrite. `mark --state PATH --step 9 --status pass --evidence FILE --note ...` chỉ dùng pass khi kiểm tra thật. `resume` tìm bước chưa đạt đầu tiên; `invalidate --from-step N --note REASON` đánh stale downstream, giữ lịch sử. ChatGPT kiểm tra fingerprints và invalidate có chủ ý. Không có hai phiên cùng ghi một state.

## Báo cáo bàn giao
Kèm đường dẫn file đã kiểm tra, size/duration/frame/codec/resolution/fps, audio/stems, subtitle, thumbnail/metadata, status 8 gates, phạm vi QC, lỗi tồn tại, quyết định chưa được duyệt, nguồn giữ nguyên và quyền xuất bản chưa kiểm chứng. Không dùng số liệu ví dụ làm số liệu job.
