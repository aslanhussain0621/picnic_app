import flet as ft
import requests
import json
import os
import datetime
import flet_fastapi

# আপনার Google Script লিঙ্ক
CLOUD_URL = "https://script.google.com/macros/s/AKfycbyU8FAhg6xtvWNPEKNSWXl28aWMnCd1qdOKANkFkXyeF7HD3XrOHOaPGLS0lLPPRysw/exec"
LOCAL_FILE = "picnic_final_db.json"

# মেম্বার লিস্ট
MEMBERS = [
    ("22121", "nazmul"), ("21664", "badsha"), ("23009", "m_kowser"), ("22330", "tansen"),
    ("22706", "islam_maynul"), ("22707", "aminul_is"), ("22716", "akonda"), ("22994", "polash"),
    ("23015", "rinku"), ("22288", "didarul_islam"), ("22446", "mejbaul"), ("22449", "md_jisan"),
    ("22452", "mahamudul"), ("22560", "aminul_rafi"), ("22862", "nazir_morsed"), ("22186", "akbar"),
    ("21355", "rahat_hasan"), ("22541", "hanif_abu"), ("22865", "m_imran"), ("22853", "md_sakil_khan"),
    ("22723", "howlader_nesar"), ("22538", "md_pappu"), ("22640", "r_rayhan"), ("21610", "rony"),
    ("22566", "malekuzzaman"), ("22576", "fazlay_rahat"), ("22692", "tanbin"), ("22725", "sabuz"),
    ("22868", "rakibul_tuhin"), ("22998", "amir_hossen"), ("21745", "md_shehab"), ("22571", "reaz"),
    ("21630", "mahim_hossain"), ("22658", "shifat_hossain"), ("22674", "abu_antor"), ("22694", "mustafizur_rahman"),
    ("22867", "al_amin_islam"), ("22981", "ratul_hasan"), ("23020", "a_ariful"), ("22453", "rakib_bepary"),
    ("22548", "wali_ullah"), ("22579", "h_masum"), ("22701", "h_hasan_mehedi"), ("22729", "jony_sheikh"),
    ("22871", "yeasin_shawon"), ("22873", "jahidul_islam_md"), ("23001", "yasin_sarkar"), ("23005", "nazrul_rabbi")
]

def main(page: ft.Page):
    page.title = "Team Nazmul Sync"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 480
    page.window_height = 850
    page.padding = 0
    page.scroll = ft.ScrollMode.ADAPTIVE

    # ডাটা হোল্ডার
    state = {"db": []}

    def load_data():
        if os.path.exists(LOCAL_FILE):
            try:
                with open(LOCAL_FILE, "r") as f: return json.load(f)
            except: pass
        return [{"id": m[0], "name": m[1], "att": False, "brk": False, "lun": False, "snk": False, "ret": False} for m in MEMBERS]

    state["db"] = load_data()

    # UI Elements
    stat_text = ft.Text(size=12, weight="bold", color="blue", text_align=ft.TextAlign.CENTER)
    sync_status = ft.Text("Last Sync: Never", size=10, italic=True, color="grey")
    list_view = ft.ListView(expand=True, spacing=0)
    search_field = ft.TextField(hint_text="Search Name or ID...", height=45, on_change=lambda e: render_list(e.control.value.lower()))

    def update_stats():
        s = {k: sum(1 for item in state["db"] if item[k]) for k in ["att", "brk", "lun", "snk", "ret"]}
        stat_text.value = f"Done: A:{s['att']} B:{s['brk']} L:{s['lun']} S:{s['snk']} R:{s['ret']}\nWait: A:{48-s['att']} B:{48-s['brk']} L:{48-s['lun']} S:{48-s['snk']} R:{48-s['ret']}"
        page.update()

    def render_list(query=""):
        list_view.controls.clear()
        for idx, item in enumerate(state["db"], 1):
            if query and query not in item['name'].lower() and query not in str(item['id']): continue
            
            # --- কালার লজিক শুরু ---
            # ডিফল্ট ব্যাকগ্রাউন্ড কালার ট্রান্সপারেন্ট (সাদা)
            row_bg = ft.colors.TRANSPARENT 
            
            # ৩ জন লিডারের নাম হলে হালকা হলুদ কালার হবে
            if item['name'].lower() in ["nazmul", "mahim_hossain", "rahat_hasan"]:
                row_bg = "#FFF9C4" # হালকা আম্বার/হলুদ কালার
            # --- কালার লজিক শেষ ---

            def on_change(e, m_id=item['id'], key=None):
                for d in state["db"]:
                    if str(d['id']) == str(m_id): d[key] = e.control.value
                with open(LOCAL_FILE, "w") as f: json.dump(state["db"], f)
                update_stats()

            list_view.controls.append(
                ft.Container(
                    bgcolor=row_bg, # এখানে কালারটি সেট করা হয়েছে
                    padding=ft.Padding(10, 0, 10, 0),
                    border=ft.border.only(bottom=ft.BorderSide(1, "#f0f0f0")),
                    content=ft.Row([
                        ft.Column([
                            ft.Text(f"{idx}. {item['name']}", size=11, weight="bold", no_wrap=True),
                            ft.Text(f"ID: {item['id']}", size=8, color="grey")
                        ], width=120, spacing=0, alignment=ft.MainAxisAlignment.CENTER),
                        ft.Checkbox(value=item['att'], on_change=lambda e, id=item['id']: on_change(e, id, 'att'), width=45),
                        ft.Checkbox(value=item['brk'], on_change=lambda e, id=item['id']: on_change(e, id, 'brk'), width=45),
                        ft.Checkbox(value=item['lun'], on_change=lambda e, id=item['id']: on_change(e, id, 'lun'), width=45),
                        ft.Checkbox(value=item['snk'], on_change=lambda e, id=item['id']: on_change(e, id, 'snk'), width=45),
                        ft.Checkbox(value=item['ret'], on_change=lambda e, id=item['id']: on_change(e, id, 'ret'), width=45),
                    ], spacing=0)
                )
            )
        page.update()

    def perform_sync(e):
        sync_button.disabled = True
        sync_status.value = "Merging Data..."
        page.update()
        
        try:
            # ১. ক্লাউড থেকে ডাটা আনা (Pull)
            pull_res = requests.get(CLOUD_URL, timeout=15)
            if pull_res.status_code == 200:
                cloud_data = pull_res.json()
                if isinstance(cloud_data, list) and len(cloud_data) > 0:
                    for i in range(len(state["db"])):
                        # মার্জ লজিক: ট্রু থাকলে ট্রুই থাকবে
                        state["db"][i]["att"] = state["db"][i]["att"] or cloud_data[i].get("att", False)
                        state["db"][i]["brk"] = state["db"][i]["brk"] or cloud_data[i].get("brk", False)
                        state["db"][i]["lun"] = state["db"][i]["lun"] or cloud_data[i].get("lun", False)
                        state["db"][i]["snk"] = state["db"][i]["snk"] or cloud_data[i].get("snk", False)
                        state["db"][i]["ret"] = state["db"][i]["ret"] or cloud_data[i].get("ret", False)

            # ২. মার্জ করা ডাটা ক্লাউডে পাঠানো (Push)
            requests.post(CLOUD_URL, data=json.dumps(state["db"]), timeout=15)
            
            # ৩. লোকাল ফাইল আপডেট
            with open(LOCAL_FILE, "w") as f: json.dump(state["db"], f)
            
            sync_status.value = f"Success: {datetime.datetime.now().strftime('%H:%M:%S')}"
            sync_status.color = "green"
        except:
            sync_status.value = "Sync Failed!"
            sync_status.color = "red"
        
        sync_button.disabled = False
        # গুরুত্বপূর্ণ: রিফ্রেশ হওয়ার পর লিস্ট নতুন করে আঁকা
        render_list(search_field.value.lower() if search_field.value else "")
        update_stats()
        page.update()

    sync_button = ft.IconButton(icon="refresh", icon_color="white", on_click=perform_sync)

    page.add(
        ft.Container(bgcolor="blue", padding=10, content=ft.Row([
            ft.Text("Team Nazmul Checklist", color="white", weight="bold", size=16),
            sync_button
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)),
        ft.Container(bgcolor="#E3F2FD", padding=5, content=ft.Column([stat_text, sync_status], horizontal_alignment="center"), alignment=ft.Alignment(0, 0)),
        ft.Container(padding=10, content=search_field),
        ft.Container(bgcolor="#f0f0f0", padding=ft.Padding(10, 5, 10, 5), content=ft.Row([
            ft.Text("Name", width=120, size=11, weight="bold"),
            ft.Text("A", width=45, size=11, weight="bold", text_align="center"),
            ft.Text("B", width=45, size=11, weight="bold", text_align="center"),
            ft.Text("L", width=45, size=11, weight="bold", text_align="center"),
            ft.Text("S", width=45, size=11, weight="bold", text_align="center"),
            ft.Text("R", width=45, size=11, weight="bold", text_align="center"),
        ], spacing=0)),
        list_view
    )

    render_list()
    update_stats()

if __name__ == "__main__": 
    app = flet_fastapi.app(main)
