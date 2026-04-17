from PIL import Image, ImageDraw, ImageFont
import datetime

def generate_multiple_schedules_image(schedules_dict, output_path="schedule.png"):
    """
    Generates a visual schedule image from 08:00 to 18:00 with 15-minute precision.
    Draws different calendars side by side in distinct columns.
    schedules_dict: { "Calendar Name": [events...] }
    """
    # Gather all events
    all_events_flat = []
    for events in schedules_dict.values():
         all_events_flat.extend(events)

    # Dynamically find the earliest start and latest end hour
    start_hour = 8
    end_hour = 18
    if all_events_flat:
        min_h = 24
        max_h = 0
        for ev in all_events_flat:
            try:
                st = ev.start_time.replace('h', ':').replace(' ', '')
                et = ev.end_time.replace('h', ':').replace(' ', '')
                sh = int(st.split(':')[0])
                eh = int(et.split(':')[0])
                em = int(et.split(':')[1]) if ':' in et else 0
                if em > 0: eh += 1
                if sh < min_h: min_h = sh
                if eh > max_h: max_h = eh
            except Exception:
                pass
        
        if min_h < 24 and min_h < start_hour: start_hour = min_h
        if max_h > 0 and max_h > end_hour: end_hour = max_h

    total_hours = end_hour - start_hour
         
    num_calendars = max(1, len(schedules_dict))
    
    # Dynamic width depending on number of columns to fit everyone comfortably
    # E.g. 1 cal = 800px, 2 = 1200px, 3 = 1600px
    width = 100 + 500 * num_calendars
    height = 1422
    header_height = 100
    hour_height = (height - header_height - 20) / total_hours
    
    bg_color = (245, 245, 245)
    line_color = (200, 200, 200)
    text_color = (50, 50, 50)
    event_colors = [
        (173, 216, 230), # Light Blue
        (144, 238, 144), # Light Green
        (255, 182, 193), # Light Pink
        (255, 228, 181), # Moccasin
        (221, 160, 221)  # Plum
    ]
    
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    def get_font(size):
        font_names = ["arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf", "FreeSans.ttf", "Arial.ttf"]
        for font_name in font_names:
            try:
                return ImageFont.truetype(font_name, size)
            except IOError:
                continue
        return ImageFont.load_default()

    font_title = get_font(36)
    font_col_title = get_font(28)
    font_time = get_font(22)
        
    def wrap_text(text, font, max_width, draw_ctx):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = " ".join(current_line + [word])
            try:
                bbox = draw_ctx.textbbox((0, 0), test_line, font=font)
                w = bbox[2] - bbox[0]
            except AttributeError:
                w, _ = draw_ctx.textsize(test_line, font=font)
            
            if w <= max_width or not current_line:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
        return lines
        
    date_str = all_events_flat[0].date if all_events_flat else datetime.datetime.now().strftime("%Y-%m-%d")
    draw.text((20, 20), f"Emploi du temps - {date_str}", font=font_title, fill=text_color)
    
    time_x = 10
    grid_x = 80
    
    for h in range(start_hour, end_hour + 1):
        y = header_height + (h - start_hour) * hour_height
        draw.text((time_x, y - 8), f"{h:02d}:00", font=font_time, fill=text_color)
        draw.line([(grid_x, y), (width - 10, y)], fill=line_color, width=2)
        if h < end_hour:
            for m in [15, 30, 45]:
                sub_y = y + int((m / 60.0) * hour_height)
                draw.line([(grid_x, sub_y), (width - 10, sub_y)], fill=(220, 220, 220), width=1)
                
    available_width = width - grid_x - 20
    col_width = available_width / num_calendars

    # Draw columns for each calendar
    for col_idx, (cal_name, events) in enumerate(schedules_dict.items()):
        col_start_x = grid_x + col_idx * col_width
        col_end_x = col_start_x + col_width - 10
        
        # Column title (User Name)
        try:
            bbox = draw.textbbox((0, 0), cal_name, font=font_col_title)
            name_width = bbox[2] - bbox[0]
        except AttributeError:
            name_width, _ = draw.textsize(cal_name, font=font_col_title)
            
        centered_x = col_start_x + (col_width - name_width) / 2
        title_y = header_height - 40
        draw.text((centered_x, title_y), cal_name, font=font_col_title, fill=text_color)
        
        # Draw vertical separator line between columns
        if col_idx > 0:
            draw.line([(col_start_x - 5, header_height), (col_start_x - 5, height - 20)], fill=line_color, width=2)
            
        # Optional: Skip drawing events if none
        if not events: pass
        
        parsed_events = []
        for idx, event in enumerate(events):
            try:
                st = event.start_time.replace('h', ':').replace(' ', '')
                et = event.end_time.replace('h', ':').replace(' ', '')
                sh, sm = map(int, st.split(':'))
                eh, em = map(int, et.split(':'))
            except ValueError:
                continue
                
            start_y = header_height + (sh - start_hour) * hour_height + (sm / 60.0) * hour_height
            end_y = header_height + (eh - start_hour) * hour_height + (em / 60.0) * hour_height
            
            if end_y <= header_height or start_y >= height - 20: continue
            
            start_y = max(header_height, start_y)
            end_y = min(header_height + total_hours * hour_height, end_y)
            
            parsed_events.append({
                "event": event, "idx": idx + col_idx*10, "start": start_y, "end": end_y
            })
            
        # Group overlapping events within this column
        parsed_events.sort(key=lambda x: (x['start'], -x['end']))
        
        groups = []
        current_group = []
        max_end = -1
        
        for pe in parsed_events:
            if not current_group:
                current_group.append(pe)
                max_end = pe['end']
            else:
                if pe['start'] < max_end:
                    current_group.append(pe)
                    max_end = max(max_end, pe['end'])
                else:
                    groups.append(current_group)
                    current_group = [pe]
                    max_end = pe['end']
        if current_group:
            groups.append(current_group)
            
        for group in groups:
            sub_columns = []
            for pe in group:
                placed = False
                for subcol_idx, subcol_end in enumerate(sub_columns):
                    if pe['start'] >= subcol_end - 0.1:
                        sub_columns[subcol_idx] = pe['end']
                        pe['col'] = subcol_idx
                        placed = True
                        break
                if not placed:
                    pe['col'] = len(sub_columns)
                    sub_columns.append(pe['end'])
                    
            num_sub_cols = len(sub_columns)
            sub_col_width = col_width / num_sub_cols
            
            for pe in group:
                event = pe['event']
                start_y = pe['start']
                end_y = pe['end']
                
                event_x_start = col_start_x + (sub_col_width * pe['col'])
                event_x_end = event_x_start + sub_col_width - 5
                
                event_bg = event_colors[pe['idx'] % len(event_colors)]
                
                draw.rectangle([(event_x_start, start_y), (event_x_end, end_y)], 
                               fill=event_bg, outline=(100, 100, 100), width=2)
                
                # Dynamic font sizing inside smaller overlapping blocks
                scale = max(0.5, 1.0 - (num_sub_cols * 0.15)) 
                f_ev_title = get_font(int(24 * scale))
                f_ev_detail = get_font(int(20 * scale))
                
                title_y = start_y + 10
                draw.text((event_x_start + 10, title_y), f"{event.start_time}-{event.end_time} | {event.type}", font=f_ev_detail, fill=(0,0,0))
                
                try:
                    bbox_time = draw.textbbox((0, 0), "A", font=f_ev_detail)
                    time_height = bbox_time[3] - bbox_time[1]
                except AttributeError:
                    _, time_height = draw.textsize("A", font=f_ev_detail)
                    
                current_y = title_y + time_height + 5  
                max_text_width = event_x_end - event_x_start - 20
                wrapped_title = wrap_text(event.name, f_ev_title, max_text_width, draw)
                
                for line in wrapped_title:
                    if current_y + 10 > end_y: break
                    draw.text((event_x_start + 10, current_y), line, font=f_ev_title, fill=(0,0,0))
                    try:
                        bbox_line = draw.textbbox((0, 0), line, font=f_ev_title)
                        current_y += (bbox_line[3] - bbox_line[1]) + 5
                    except AttributeError:
                        _, h = draw.textsize(line, font=f_ev_title)
                        current_y += h + 5
                
                details = []
                if event.room: details.append(event.room)
                if event.trainers: details.append(", ".join(event.trainers))
                
                if details:
                    details_text = " | ".join(details)
                    wrapped_details = wrap_text(details_text, f_ev_detail, max_text_width, draw)
                    try:
                        bbox_detail = draw.textbbox((0, 0), "A", font=f_ev_detail)
                        detail_height = bbox_detail[3] - bbox_detail[1]
                    except AttributeError:
                        _, detail_height = draw.textsize("A", font=f_ev_detail)
                        
                    total_details_height = len(wrapped_details) * (detail_height + 5)
                    
                    if current_y + total_details_height + 10 <= end_y:
                         current_y += 5
                         for line in wrapped_details:
                             draw.text((event_x_start + 10, current_y), line, font=f_ev_detail, fill=(50,50,50))
                             current_y += detail_height + 5

    img.save(output_path)
    return output_path
