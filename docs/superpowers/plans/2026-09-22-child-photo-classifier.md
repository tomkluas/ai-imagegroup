# 儿童照片离线分类软件实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个可在 Windows 10/11 普通办公电脑上离线管理儿童参考照、批量识别人脸、人工复核并按姓名复制照片的桌面应用。

**Architecture:** 使用 PySide6 构建桌面界面，SQLite 保存领域数据，OpenCV YuNet/SFace 提供可替换的识别后端，有界任务流水线负责扫描、识别和复制。界面只调用应用服务；模型、数据库和文件输出分别封装，以便独立测试与替换。

**Tech Stack:** Python 3.12、PySide6、OpenCV、NumPy、psutil、SQLite、pytest、pytest-qt、PyInstaller、Inno Setup（安装包）

**Spec:** `docs/superpowers/specs/2026-09-22-child-photo-classifier-design.md`

## Global Constraints

- 仅支持 64 位 Windows 10/11，最终用户无需安装 Python、数据库、CUDA 或其他运行环境。
- 全部识别离线完成；不得上传照片、人脸特征、日志或使用情况。
- 目标规模为 50 名小朋友、每人 3～5 张参考照、每批约 500 张 3456×4608、2～10MB 照片。
- 输入原图永不修改、移动或删除；多人照片向每位已识别儿童目录各复制一份。
- 自动分类优先降低误认；低可信进入人工确认，远景、遮挡、后脑勺和无法可靠判断的人脸允许不分类。
- 在约定 2 核、8GB、无独显目标电脑和代表性 500 张真实照片上，纯识别阶段必须不超过 2 分钟；模型预热、首次参考库建立和原图复制分别计时。
- 支持 JPG、JPEG、PNG、BMP、WebP、中文路径、中文姓名和 EXIF 方向。
- 默认硬件探测失败时按 2 核、8GB、2 个工作线程运行。
- 模型版本、来源、许可证和 SHA-256 必须随发布物记录；运行时不下载模型。

## Review Focus

- 两个儿童非常相似且第一、第二候选接近时，必须进入人工确认而不是自动归类；由 Task 4 的差距门槛测试覆盖。
- 同一照片通过不同路径或重复选择加入时，任务内只处理一次；由 Task 5 的内容指纹测试覆盖。
- 中文路径、EXIF 旋转和同名输出文件不得导致错误方向或覆盖；由 Task 5 的图像与冲突命名测试覆盖。
- 输出磁盘在识别完成后空间不足时，识别记录必须保留且复制可恢复；由 Task 6 的暂停/恢复测试覆盖。
- 删除儿童时不得删除用户源文件，但必须清除应用副本与特征；由 Task 2 的删除边界测试覆盖。

---

## 文件结构

```text
pyproject.toml                         # 依赖、pytest、ruff 和打包入口
src/image_group/app.py                # QApplication 入口与依赖装配
src/image_group/domain/models.py      # 领域枚举和不可变数据类型
src/image_group/storage/database.py   # SQLite 连接、事务与迁移
src/image_group/storage/repositories.py # People、photos、tasks 仓储
src/image_group/people/service.py     # 儿童和参考照应用服务
src/image_group/recognition/base.py   # 识别后端协议与结果类型
src/image_group/recognition/opencv_backend.py # YuNet/SFace 后端
src/image_group/recognition/policy.py # 自动/复核/未识别判定
src/image_group/photos/io.py          # EXIF、分析图、缩略图和格式读取
src/image_group/tasks/scanner.py      # 输入扫描、指纹和去重
src/image_group/tasks/runner.py       # 有界识别流水线与恢复
src/image_group/output/service.py     # 原图复制、冲突命名和修正
src/image_group/hardware/profile.py   # 硬件探测、档位和并发方案
src/image_group/ui/main_window.py     # 主窗口与导航
src/image_group/ui/people_page.py     # 小朋友和参考照管理
src/image_group/ui/new_task_page.py   # 新建任务和进度
src/image_group/ui/review_page.py     # 人工确认
src/image_group/ui/results_page.py    # 任务历史和结果修正
src/image_group/ui/settings_page.py   # 性能档位、备份和数据操作
src/image_group/backup/service.py     # 参考库备份与恢复
src/image_group/reports/csv_report.py # UTF-8 BOM CSV 报告
resources/models/                     # 固定版本 ONNX 模型及 LICENSE
packaging/image-group.spec            # PyInstaller 配置
packaging/installer.iss                # Inno Setup 安装脚本
tests/                                # 与 src 结构对应的单元/集成/UI 测试
benchmarks/run_batch.py               # 500 张实机性能工具
```

### Task 1: 项目骨架、领域类型与 SQLite 迁移

**Files:**
- Create: `pyproject.toml`
- Create: `src/image_group/domain/models.py`
- Create: `src/image_group/storage/database.py`
- Create: `src/image_group/storage/repositories.py`
- Create: `tests/storage/test_database.py`
- Create: `tests/storage/test_repositories.py`

**Interfaces:**
- Produces: `Database(path: Path)`, `Database.transaction()`, `PersonRepository`, `TaskRepository`, `Person`, `ReferencePhoto`, `ClassificationTask`, `FaceDecision`。

- [ ] **Step 1: 写数据库迁移失败测试**

```python
def test_new_database_has_schema_and_foreign_keys(tmp_path):
    db = Database(tmp_path / "data.db")
    db.migrate()
    assert db.scalar("PRAGMA user_version") == 1
    assert db.scalar("PRAGMA foreign_keys") == 1
    assert {"people", "reference_photos", "tasks", "task_photos", "faces", "assignments"} <= db.table_names()
```

- [ ] **Step 2: 运行测试并确认因模块不存在而失败**

Run: `python -m pytest tests/storage/test_database.py -v`
Expected: FAIL，`ModuleNotFoundError: image_group`。

- [ ] **Step 3: 建立可安装包和迁移 v1**

在 `pyproject.toml` 配置 `src` 布局、`image-group = image_group.app:main`、pytest `testpaths=["tests"]`。在 `Database.migrate()` 中一次事务创建六张表、索引、外键和 `PRAGMA user_version=1`；连接统一启用 `foreign_keys=ON`、`journal_mode=WAL`、`busy_timeout=5000`。

- [ ] **Step 4: 添加仓储往返与事务回滚测试**

```python
def test_person_round_trip_and_duplicate_display_name(tmp_path):
    repo = make_person_repo(tmp_path)
    alice = repo.create("张小明")
    assert repo.get(alice.id) == alice
    with pytest.raises(DuplicateNameError):
        repo.create("张小明")

def test_transaction_rolls_back_all_writes(db):
    with pytest.raises(RuntimeError), db.transaction():
        db.execute("INSERT INTO people(id, display_name) VALUES (?, ?)", ("p1", "甲"))
        raise RuntimeError("stop")
    assert db.scalar("SELECT count(*) FROM people") == 0
```

- [ ] **Step 5: 实现领域类型和仓储并运行测试**

`FaceDecision` 固定为 `AUTO`、`REVIEW`、`UNKNOWN`；所有 ID 使用 UUID 字符串；所有数据库时间使用 UTC ISO-8601。Run: `python -m pytest tests/storage -v`，Expected: PASS。

- [ ] **Step 6: 初始化 Git 并提交**

Run: `git init && git add pyproject.toml src tests && git commit -m "feat: bootstrap domain storage"`

### Task 2: 小朋友与参考照片管理

**Files:**
- Create: `src/image_group/people/service.py`
- Create: `tests/people/test_service.py`
- Modify: `src/image_group/storage/repositories.py`

**Interfaces:**
- Consumes: `PersonRepository`, `Database.transaction()`。
- Produces: `PeopleService.create_person(name)`, `rename_person(person_id, name)`, `import_reference(person_id, source)`, `delete_reference(id)`, `delete_person(id)`, `bulk_import(root)`。
- `import_reference` 暂时调用注入的 `ReferenceValidator.validate(path) -> ValidatedReference`，由 Task 3 提供真实实现。

- [ ] **Step 1: 写导入、同名、非法名和删除边界测试**

```python
def test_import_copies_source_and_delete_never_removes_source(service, tmp_path):
    source = tmp_path / "源照片.jpg"; source.write_bytes(b"jpeg")
    person = service.create_person("张小明")
    ref = service.import_reference(person.id, source)
    assert ref.managed_path.read_bytes() == b"jpeg"
    service.delete_person(person.id)
    assert source.exists()
    assert not ref.managed_path.exists()

@pytest.mark.parametrize("name", ["", "CON", "张/小明", "张小明."])
def test_invalid_windows_names_are_rejected(service, name):
    with pytest.raises(InvalidPersonNameError): service.create_person(name)
```

- [ ] **Step 2: 运行并确认失败**

Run: `python -m pytest tests/people/test_service.py -v`，Expected: FAIL，服务不存在。

- [ ] **Step 3: 实现原子导入与删除**

管理副本命名为 `<uuid><lowercase suffix>`，先复制到同目录临时文件、`fsync` 后原子替换，再写数据库；数据库失败则删除新副本。删除先将应用副本移入应用内回收暂存区，数据库提交后清除，失败则恢复。源文件路径只作审计记录，任何删除路径必须验证位于应用 `reference/` 根目录内。

- [ ] **Step 4: 写姓名目录批量导入测试并实现**

```python
def test_bulk_import_uses_child_directory_as_name(service, sample_tree):
    result = service.bulk_import(sample_tree)
    assert result.created_people == ["张小明", "李小红"]
    assert result.imported_count == 6
```

忽略根目录散落文件和嵌套二级目录，返回逐文件失败原因；一个儿童少于三张有效照片时返回 warning，不阻止保存。

- [ ] **Step 5: 运行测试并提交**

Run: `python -m pytest tests/people tests/storage -v`，Expected: PASS。Commit: `git commit -am "feat: manage people and references"`。

### Task 3: 图片读取与 OpenCV 人脸后端

**Files:**
- Create: `src/image_group/photos/io.py`
- Create: `src/image_group/recognition/base.py`
- Create: `src/image_group/recognition/opencv_backend.py`
- Create: `tests/photos/test_io.py`
- Create: `tests/recognition/test_opencv_backend.py`
- Add: `resources/models/face_detection_yunet_2023mar.onnx`
- Add: `resources/models/face_recognition_sface_2021dec.onnx`
- Add: `resources/models/MODELS.json`
- Add: `resources/models/LICENSES.txt`

**Interfaces:**
- Produces: `ImageLoader.analysis_image(path, max_long_edge) -> LoadedImage`, `RecognitionBackend.validate_reference(path) -> ValidatedReference`, `detect_and_embed(image) -> list[DetectedFace]`。
- `DetectedFace` 包含 `box`, `landmarks`, `detection_score`, `face_size`, `embedding: np.ndarray`。

- [ ] **Step 1: 写 EXIF 旋转、中文路径和分析尺寸测试**

```python
def test_analysis_image_applies_orientation_and_bounds_long_edge(oriented_jpeg):
    loaded = ImageLoader().analysis_image(oriented_jpeg, 1280)
    assert loaded.image.shape[:2] == (960, 1280)
    assert loaded.orientation_applied is True

def test_unicode_path_round_trip(unicode_jpeg):
    assert ImageLoader().analysis_image(unicode_jpeg, 960).image.size > 0
```

- [ ] **Step 2: 实现 `np.fromfile` + `cv2.imdecode` 读取和 EXIF 方向处理**

保留源尺寸与缩放比例，使检测框可映射回原图；损坏图片抛出带路径的 `ImageDecodeError`。Run: `python -m pytest tests/photos -v`，Expected: PASS。

- [ ] **Step 3: 写后端合约测试**

```python
def test_reference_rejects_zero_or_multiple_faces(backend, no_face, two_faces):
    with pytest.raises(ReferenceValidationError, match="未检测到"):
        backend.validate_reference(no_face)
    with pytest.raises(ReferenceValidationError, match="多张"):
        backend.validate_reference(two_faces)

def test_detect_and_embed_returns_l2_normalized_vectors(backend, group_photo):
    faces = backend.detect_and_embed(group_photo)
    assert len(faces) >= 2
    assert all(np.isclose(np.linalg.norm(f.embedding), 1.0, atol=1e-4) for f in faces)
```

- [ ] **Step 4: 固定模型并记录元数据**

从 OpenCV Zoo 官方发布获取两份模型，`MODELS.json` 记录文件名、上游 URL、版本、许可证和 SHA-256。启动时逐个校验；缺失或不匹配抛出 `ModelIntegrityError`，不得联网下载。

- [ ] **Step 5: 实现 YuNet/SFace 后端**

用 `cv2.FaceDetectorYN.create` 检测，用五点关键点 `alignCrop` 后 `feature`；统一将结果 `float32` L2 归一化。参考照要求恰好一个显著人脸，脸框最短边至少 80 分析像素，且检测分数达到配置门槛。

- [ ] **Step 6: 运行测试并提交**

Run: `python -m pytest tests/photos tests/recognition/test_opencv_backend.py -v`，Expected: PASS。Commit: `git commit -am "feat: add offline face recognition backend"`。

### Task 4: 相似度、保守判定与校准配置

**Files:**
- Create: `src/image_group/recognition/policy.py`
- Create: `tests/recognition/test_policy.py`
- Modify: `src/image_group/domain/models.py`

**Interfaces:**
- Consumes: `DetectedFace.embedding`、`dict[person_id, list[np.ndarray]]`。
- Produces: `DecisionPolicy.classify(face, gallery) -> FaceMatch`；`FaceMatch` 包含 top-3 `Candidate`、`decision` 和 `reason`。

- [ ] **Step 1: 写三路分流和相近候选测试**

```python
def test_close_first_and_second_candidates_require_review(policy, face, gallery):
    match = policy.classify(face, gallery_with_scores(0.62, 0.60))
    assert match.decision is FaceDecision.REVIEW
    assert match.reason == "ambiguous_margin"

def test_low_quality_or_low_score_is_unknown(policy, low_quality_face, gallery):
    assert policy.classify(low_quality_face, gallery).decision is FaceDecision.UNKNOWN
```

- [ ] **Step 2: 实现纯函数判定策略**

每位儿童得分取其参考向量中最高余弦相似度；按得分降序取前三。默认阈值只作为开发初值并写入版本化配置：`auto_score=0.50`、`review_score=0.36`、`auto_margin=0.08`、`min_face_size=40`；生产发布前必须由校准数据替换并写入测试报告。

- [ ] **Step 3: 增加空图库、单候选、多参考照和 NaN 测试**

空图库与非有限向量返回 UNKNOWN；单候选无需伪造第二名；同一儿童多张参考照只产生一个候选。

- [ ] **Step 4: 运行测试并提交**

Run: `python -m pytest tests/recognition -v`，Expected: PASS。Commit: `git commit -am "feat: add conservative recognition policy"`。

### Task 5: 输入扫描、去重与安全输出

**Files:**
- Create: `src/image_group/tasks/scanner.py`
- Create: `src/image_group/output/service.py`
- Create: `tests/tasks/test_scanner.py`
- Create: `tests/output/test_service.py`

**Interfaces:**
- Produces: `PhotoScanner.scan(paths) -> ScanResult`、`OutputService.materialize(task_id, source, person_ids)`、`remove_assignment(...)`、`add_assignment(...)`。

- [ ] **Step 1: 写格式过滤、内容去重与递归边界测试**

```python
def test_same_content_selected_by_two_paths_is_scanned_once(scanner, jpg, alias_copy):
    result = scanner.scan([jpg, alias_copy])
    assert len(result.photos) == 1
    assert len(result.duplicates) == 1
```

目录输入只扫描该目录直接包含的支持格式图片，避免意外吞入历史输出子目录；多选文件按显式列表处理。指纹先用大小和快速分块哈希筛选，再用 SHA-256 确认重复。

- [ ] **Step 2: 实现扫描器并运行测试**

Run: `python -m pytest tests/tasks/test_scanner.py -v`，Expected: PASS。

- [ ] **Step 3: 写多人复制、同名冲突和源文件保护测试**

```python
def test_group_photo_is_copied_once_per_distinct_person(output, source):
    paths = output.materialize("t1", source, ["p1", "p2", "p1"])
    assert set(paths) == {output.person_dir("p1") / source.name,
                         output.person_dir("p2") / source.name}
    assert source.exists()

def test_same_filename_different_content_never_overwrites(output, first, second):
    a = output.materialize("t1", first, ["p1"])[0]
    b = output.materialize("t1", second, ["p1"])[0]
    assert a != b and a.read_bytes() != b.read_bytes()
```

- [ ] **Step 4: 实现可恢复文件操作**

复制到目标目录临时文件，校验大小后原子改名；冲突名使用 `<stem>_<sha256前8位><suffix>`。数据库 assignment 记录 `pending_copy/copied/copy_failed/pending_delete`；修正结果先写意图再操作文件，启动恢复器重放未完成操作。

- [ ] **Step 5: 运行测试并提交**

Run: `python -m pytest tests/tasks tests/output -v`，Expected: PASS。Commit: `git commit -am "feat: scan and materialize photo results"`。

### Task 6: 硬件配置与可恢复任务流水线

**Files:**
- Create: `src/image_group/hardware/profile.py`
- Create: `src/image_group/tasks/runner.py`
- Create: `tests/hardware/test_profile.py`
- Create: `tests/tasks/test_runner.py`

**Interfaces:**
- Produces: `HardwareProfiler.detect() -> HardwareProfile`、`ConcurrencyPlanner.plan(profile, mode) -> RuntimePlan`、`TaskRunner.start(task_id)`、`cancel(task_id)`、`resume(task_id)`。
- `TaskRunner` 通过回调发出不可变 `ProgressEvent`，不依赖 Qt。

- [ ] **Step 1: 写探测失败回退与档位上限测试**

```python
def test_probe_failure_uses_two_core_eight_gb_defaults(failing_probe):
    p = HardwareProfiler(failing_probe).detect()
    assert (p.logical_cpus, p.total_memory_gb, p.fallback) == (2, 8, True)
    assert ConcurrencyPlanner().plan(p, "balanced").recognition_workers == 2
```

- [ ] **Step 2: 实现探测和有界配置**

读取逻辑核心、总/可用内存、磁盘空间；无法可靠判断磁盘类型时按机械盘策略。允许节能/均衡/高速，但识别 worker 不超过逻辑核心且任务开始时可因可用内存不足下调。

- [ ] **Step 3: 写任务状态机、取消、异常与磁盘不足恢复测试**

```python
def test_disk_full_preserves_recognition_and_resume_only_retries_copy(runner, disk_full_output):
    runner.start("t1")
    assert runner.state("t1") == "copy_paused"
    assert runner.recognized_count("t1") == 3
    disk_full_output.make_space()
    runner.resume("t1")
    assert runner.state("t1") == "completed"
    assert disk_full_output.recognition_calls == 3
```

- [ ] **Step 4: 实现三阶段有界流水线**

阶段为 decode、recognize、copy；队列容量由 `RuntimePlan` 给出。每张照片识别结束立即事务落盘；取消停止投递新项目，等待当前最小单元结束后标记 cancelled；单图异常写入 task_photo error 并继续。

- [ ] **Step 5: 运行测试并提交**

Run: `python -m pytest tests/hardware tests/tasks tests/output -v`，Expected: PASS。Commit: `git commit -am "feat: run recoverable adaptive classification tasks"`。

### Task 7: 主窗口与小朋友管理界面

**Files:**
- Create: `src/image_group/app.py`
- Create: `src/image_group/ui/main_window.py`
- Create: `src/image_group/ui/people_page.py`
- Create: `src/image_group/ui/settings_page.py`
- Create: `tests/ui/test_people_page.py`

**Interfaces:**
- Consumes: `PeopleService`、`HardwareProfiler`。
- Produces: `MainWindow` 和可通过 Qt signals 调用的页面操作。

- [ ] **Step 1: 写导航与新增儿童 UI 测试**

```python
def test_add_person_refreshes_list(qtbot, window, people_service):
    qtbot.mouseClick(window.people_page.add_button, Qt.LeftButton)
    window.people_page.name_dialog.name_edit.setText("张小明")
    qtbot.mouseClick(window.people_page.name_dialog.ok_button, Qt.LeftButton)
    assert window.people_page.person_names() == ["张小明"]
```

- [ ] **Step 2: 实现主窗口和五页导航骨架**

主窗口包含小朋友管理、新建任务、人工确认、分类结果、设置；页面按需创建。异常通过统一中文错误对话框展示，后台任务不得阻塞 UI 线程。

- [ ] **Step 3: 实现参考照网格、拖放和质量提示**

参考照导入使用 `PeopleService`；失败项逐张显示原因；少于三张显示黄色提示；删除弹出二次确认并明确“不删除原始来源文件”。缩略图只读取应用管理副本。

- [ ] **Step 4: 实现设置页性能档位与重新检测**

显示探测到的 CPU/内存、当前方案及 fallback 状态；三个档位为互斥选择，重新检测后刷新方案但不影响运行中任务。

- [ ] **Step 5: 运行测试并提交**

Run: `python -m pytest tests/ui/test_people_page.py -v`，Expected: PASS。Commit: `git commit -am "feat: add people management desktop UI"`。

### Task 8: 新建任务、人工确认与结果浏览界面

**Files:**
- Create: `src/image_group/ui/new_task_page.py`
- Create: `src/image_group/ui/review_page.py`
- Create: `src/image_group/ui/results_page.py`
- Create: `tests/ui/test_task_workflow.py`

**Interfaces:**
- Consumes: `PhotoScanner`、`TaskRunner`、repositories、`OutputService`。

- [ ] **Step 1: 写新任务选择、空间校验和进度测试**

测试文件夹与多文件两种选择、儿童勾选、不可写输出阻止开始，以及 `ProgressEvent` 到总数/完成数/识别耗时/复制耗时标签的映射。

- [ ] **Step 2: 实现新建任务页**

扫描在后台线程执行；显示缩略图、数量、估算体积和重复数。任务名默认时间，输出目录必选；开始按钮仅在输入、至少一名儿童和可写输出均有效时启用。

- [ ] **Step 3: 写 top-3 人工确认测试并实现页面**

展示整图和映射回原图的人脸框；提供 top-3、姓名搜索、“不是这些人”和“跳过”。确认只新增当前 assignment；“同时加入参考照片”为独立且默认不勾选的操作。

- [ ] **Step 4: 写结果修正与懒加载测试并实现页面**

仅为可见网格项请求缩略图；选择儿童过滤结果；添加/移除 assignment 调用 `OutputService`；“打开目录”只打开当前任务已验证的输出根目录。

- [ ] **Step 5: 运行 UI 与全量测试并提交**

Run: `python -m pytest tests/ui tests/tasks tests/output -v`，Expected: PASS。Commit: `git commit -am "feat: complete classification review workflow"`。

### Task 9: 报告、备份、恢复与隐私边界

**Files:**
- Create: `src/image_group/reports/csv_report.py`
- Create: `src/image_group/backup/service.py`
- Create: `tests/reports/test_csv_report.py`
- Create: `tests/backup/test_service.py`
- Modify: `src/image_group/ui/settings_page.py`

**Interfaces:**
- Produces: `CsvReport.write(task_id, path)`、`BackupService.create(path)`、`inspect(path)`、`restore(path)`。

- [ ] **Step 1: 写中文 Excel 兼容 CSV 和公式注入测试**

```python
def test_csv_has_bom_and_escapes_formula_cells(report, tmp_path):
    path = report.write("t1", tmp_path / "报告.csv")
    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    assert "'=" in raw.decode("utf-8-sig")
```

- [ ] **Step 2: 实现固定列报告**

列为源照片、SHA-256、儿童姓名、判定来源（自动/人工）、状态、错误、完成时间；以 UTF-8 BOM 写入，任何以 `= + - @` 开头的用户字符串前加单引号。

- [ ] **Step 3: 写备份校验、版本拒绝和路径穿越测试**

备份为 ZIP，包含数据库一致性快照、参考副本、特征、配置和 manifest SHA-256；恢复前验证全部条目、拒绝 `../` 或绝对路径、拒绝高于当前支持版本。

- [ ] **Step 4: 实现备份/恢复和彻底删除入口**

恢复先解压到应用目录内临时区并完成校验，再原子切换；失败保持旧数据。设置页明确列出被删除的是应用副本/特征/记录而非用户源照片。

- [ ] **Step 5: 运行测试并提交**

Run: `python -m pytest tests/reports tests/backup tests/people -v`，Expected: PASS。Commit: `git commit -am "feat: add reports and local data backup"`。

### Task 10: 集成验收、性能基准与 Windows 打包

**Files:**
- Create: `tests/integration/test_end_to_end.py`
- Create: `benchmarks/run_batch.py`
- Create: `packaging/image-group.spec`
- Create: `packaging/installer.iss`
- Create: `docs/user-guide.md`
- Create: `THIRD_PARTY_NOTICES.md`
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: 安装版 `.exe`、便携版目录、性能 JSON、准确率/性能报告。

- [ ] **Step 1: 写端到端测试**

使用可控 fake backend 建立两名儿童、导入参考照、扫描一张多人照片、产生一个 AUTO 和一个 REVIEW、人工确认、复制到两个目录、修正一项并导出 CSV；断言数据库、界面服务和文件结果一致。

- [ ] **Step 2: 运行全量测试和静态检查**

Run: `python -m pytest -v`，Expected: PASS。Run: `python -m ruff check src tests benchmarks`，Expected: zero errors。

- [ ] **Step 3: 实现性能工具并建立基线**

`benchmarks/run_batch.py --input <dir> --references <dir> --json <file>` 输出硬件、模型 SHA、照片数量、总像素、扫描/解码/检测/识别/写库/复制分段耗时、峰值 RSS、错误数；支持 `--recognition-only` 排除复制。

- [ ] **Step 4: 在目标电脑执行 500 张实机验收**

先预热一次模型，再运行至少三次 `--recognition-only`，使用中位数；要求不超过 120 秒。若超时，依据分段数据依次验证内嵌缩略图、960/1280 分辨率、OpenCV 内部线程数和 worker 组合；每次优化必须重跑准确率集，不能降低安全门槛。未达到 120 秒不得标记性能验收通过。

- [ ] **Step 5: 完成真实样本阈值校准**

用严格分离的参考集和标注测试集搜索 `auto_score/review_score/auto_margin/min_face_size`；选择满足用户认可误认率的最保守组合，将值、样本统计和混淆情况写入发布报告。没有真实样本时保留开发初值但发布物标记“未完成生产校准”，不得声称达到准确率验收。

- [ ] **Step 6: 打包并验证干净系统**

PyInstaller 收集 Qt 插件、模型、许可证和迁移资源；启动时模型路径通过 `sys._MEIPASS`/应用资源根解析。Inno Setup 安装到用户可写应用目录，默认保留应用数据。分别在干净 Windows 10/11 64 位虚拟机测试安装、启动、中文路径分类、卸载保留数据和显式清除数据。

- [ ] **Step 7: 编写用户说明和第三方声明**

说明参考照要求、四页工作流、人工确认、备份恢复、性能档位、隐私责任和“不识别后脑勺”等边界；列出 Python、PySide6、OpenCV、NumPy、psutil、YuNet、SFace、PyInstaller 许可证与来源。

- [ ] **Step 8: 最终验证并提交**

Run: `python -m pytest -v`、`python -m ruff check src tests benchmarks`、打包 smoke test 和安装 smoke test，全部成功后提交：`git commit -am "build: package validated Windows application"`。

## 完成定义

- 所有自动化测试、静态检查、Windows 10/11 安装测试通过。
- 真实样本阈值已经校准，或发布物明确标记尚未完成生产校准。
- 目标电脑 500 张纯识别中位数不超过 120 秒，否则性能验收不得标记通过。
- 原图保护、多人物复制、人工确认、结果修正、恢复和备份均有自动化覆盖。
- 安装包、便携版、源代码、许可证清单、用户手册和测试报告齐全。
