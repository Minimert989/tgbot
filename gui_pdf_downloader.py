import os, time, threading, asyncio
from tkinter import Tk, StringVar, Text, END, Button, Entry, Label, filedialog, simpledialog, messagebox
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv

# .env에서 기본값 로드(있으면)
load_dotenv()
DEF_API_ID = os.getenv("API_ID", "")
DEF_API_HASH = os.getenv("API_HASH", "")

def gui_log(widget: Text, msg: str):
    widget.insert(END, msg + "\n")
    widget.see(END)

async def ensure_login(client: TelegramClient, root, log: Text):
    await client.connect()
    if await client.is_user_authorized():
        return
    phone = simpledialog.askstring("로그인", "전화번호(+82… 형식):", parent=root)
    if not phone:
        raise SystemExit("전화번호 필요")
    await client.send_code_request(phone)
    code = simpledialog.askstring("인증코드", "Telegram 앱의 5자리 코드:", parent=root)
    if not code:
        raise SystemExit("인증코드 필요")
    try:
        await client.sign_in(phone=phone, code=code)
    except SessionPasswordNeededError:
        pw = simpledialog.askstring("2단계 인증", "비밀번호:", parent=root, show="*")
        await client.sign_in(password=pw)
    gui_log(log, "로그인 완료")

async def progress_cb(current, total, file_name, start_time, log: Text):
    percent = (current / total * 100) if total else 0.0
    speed = current / max(1e-6, (time.time() - start_time))
    log_str = f"{file_name} {percent:.1f}% | {speed/1024:.1f} KB/s"
    log.after(0, gui_log, log, log_str)

async def download_pdf(message, out_dir, downloaded: set, log: Text):
    if not (message.document and message.document.mime_type == "application/pdf"):
        return False
    try:
        attrs = message.document.attributes or []
        file_name = None
        for a in attrs:
            if hasattr(a, "file_name") and a.file_name:
                file_name = a.file_name
                break
        if not file_name:
            file_name = f"{message.id}.pdf"
    except Exception:
        file_name = f"{message.id}.pdf"

    if file_name in downloaded:
        log.after(0, gui_log, log, f"skip: {file_name}")
        return False

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, file_name)
    start = time.time()
    try:
        await message.download_media(
            path,
            progress_callback=lambda c, t: asyncio.create_task(
                progress_cb(c, t, file_name, start, log)
            ),
        )
        downloaded.add(file_name)
        log.after(0, gui_log, log, f"done: {file_name}")
        return True
    except Exception as e:
        log.after(0, gui_log, log, f"fail: {file_name} -> {e}")
        return False

async def run_job(api_id: int, api_hash: str, channel_input: str, out_dir: str, log: Text):
    client = TelegramClient("pdf_gui_session", api_id, api_hash)
    async with client:
        await ensure_login(client, log.master, log)
        # 채널 입력: 숫자(ID) 또는 @username 지원
        try:
            entity = int(channel_input)
        except ValueError:
            entity = await client.get_entity(channel_input.strip())

        log_file = os.path.join(out_dir, "downloads.txt")
        downloaded = set()
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                downloaded = set(f.read().splitlines())

        gui_log(log, f"start channel={channel_input}, out={out_dir}")
        offset_id = 0
        batch_size = 100
        new_count = 0

        while True:
            messages = [m async for m in client.iter_messages(entity, limit=batch_size, offset_id=offset_id, reverse=True)]
            if not messages:
                break
            gui_log(log, f"batch {len(messages)}")
            results = await asyncio.gather(*[download_pdf(m, out_dir, downloaded, log) for m in messages])
            new_count += sum(bool(r) for r in results)
            offset_id = messages[-1].id
            await asyncio.sleep(0.5)

        if new_count:
            with open(log_file, "w") as f:
                for name in sorted(downloaded):
                    f.write(name + "\n")
        gui_log(log, f"finished. new downloads: {new_count}")

def main():
    root = Tk()
    root.title("Telegram PDF Downloader")

    api_id_var = StringVar(value=DEF_API_ID)
    api_hash_var = StringVar(value=DEF_API_HASH)
    chan_var = StringVar()
    out_var = StringVar(value=os.path.expanduser("~/Desktop/Telegram_PDFs"))

    Label(root, text="API_ID").grid(row=0, column=0, sticky="w")
    Entry(root, textvariable=api_id_var, width=28).grid(row=0, column=1, sticky="we")

    Label(root, text="API_HASH").grid(row=1, column=0, sticky="w")
    Entry(root, textvariable=api_hash_var, width=28).grid(row=1, column=1, sticky="we")

    Label(root, text="Channel ID/@username").grid(row=2, column=0, sticky="w")
    Entry(root, textvariable=chan_var, width=28).grid(row=2, column=1, sticky="we")

    Label(root, text="Download Dir").grid(row=3, column=0, sticky="w")
    Entry(root, textvariable=out_var, width=28).grid(row=3, column=1, sticky="we")
    Button(root, text="Browse", command=lambda: out_var.set(filedialog.askdirectory() or out_var.get())).grid(row=3, column=2)

    log = Text(root, height=18, width=70)
    log.grid(row=4, column=0, columnspan=3, pady=6)

    def start():
        try:
            api_id = int(api_id_var.get().strip())
        except Exception:
            messagebox.showerror("오류", "API_ID 숫자 필요")
            return
        api_hash = api_hash_var.get().strip()
        if not api_hash:
            messagebox.showerror("오류", "API_HASH 필요")
            return
        channel_input = chan_var.get().strip()
        if not channel_input:
            messagebox.showerror("오류", "Channel ID 또는 @username 입력")
            return
        out_dir = out_var.get().strip()
        if not out_dir:
            messagebox.showerror("오류", "다운로드 폴더 필요")
            return

        def runner():
            try:
                asyncio.run(run_job(api_id, api_hash, channel_input, out_dir, log))
            except Exception as e:
                log.after(0, gui_log, log, f"에러: {e}")

        threading.Thread(target=runner, daemon=True).start()

    Button(root, text="Start", command=start).grid(row=5, column=0, pady=4)
    Button(root, text="Quit", command=root.destroy).grid(row=5, column=2, pady=4)
    root.mainloop()

if __name__ == "__main__":
    main()