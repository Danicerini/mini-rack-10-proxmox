// =====================================================================
//  CASA Rack 10" - mini rack stampabile per il cluster Proxmox
//  Stile "mini-rack a telaio": cornici sopra/sotto arrotondate, 4 montanti forati,
//  pannelli laterali a nido d'ape, maniglie sopra e piedini sotto (stessa foratura).
//  Standard 10": pannelli 254 mm, 1U = 44.45 mm, 3 fori per U (schema EIA).
//  Dall'alto: 2U plancia inclinata 10 gradi (switch ed ESP32 dietro) | 1U pve3 (HP 800 G5) | 1U pve2 (HP 800 G2)
//             | base da 51 mm per pve1 (Teclast N30, alto 43.5 mm), sopra si riprende lo standard
//  Viti apparati: M6 con dado M6 nella sede sul retro dei montanti.
//  Telaio: viti autofilettanti 4 mm; pannelli laterali: autofilettanti 3 mm.
//  Tutti i pezzi stanno nel piatto 256x256 della Bambu Lab A1.
//
//  part = "assembly" | "post_low" | "post_high" | "ring_bottom" | "ring_top"
//       | "side_low_dx" | "side_low_sx" | "side_high_dx" | "side_high_sx" | "handle" | "foot"
//       | "shelf_hp" | "shelf_base" | "shelf_control" | "face_hp" | "face_base" | "face_control"
//  label = testo inciso sui ripiani PC (es. "pve1")
// =====================================================================
part  = "assembly";
show_pcs = true;   // sagome dei PC nel montaggio
label = "pve1";
$fn = 40;

// ---------------- Standard 10" ----------------
U       = 44.45;
NU      = 4;           // unita' standard sopra la base
base_h  = 51;          // piano in basso: mini PC alto 45 mm
tilt    = 10;           // inclinazione plancia (gradi)
r_face  = 4;            // raggio angoli pannelli frontali
PW      = 254;          // larghezza esterna (= pannelli)
post    = 18;           // sezione montanti
EAR     = post / 2;     // fori al centro dei montanti (interasse 236 mm)
U_ALL   = [6.35, 22.225, 38.1];   // 3 fori per U sui montanti
U_HOLES = [6.35, 38.1];           // fori usati da ripiani e pannelli
// quote dei fori di un tratto di montante: prima la base (se c'e'), poi le unita' standard
function m6_z(nu, base)   = concat(base > 0 ? [6.35, base / 2, base - 6.35] : [], [for (u = [0 : nu - 1], hz = U_ALL) base + u * U + hz]);
function side_z(nu, base) = concat(base > 0 ? [14, base - 14] : [], [for (u = [0 : nu - 1]) base + u * U + 14]);
screw_d = 6.5;                    // M6
nut_d   = 12.0;  nut_h = 5.4;     // dado M6 (10 mm in chiave)
st4_pilot = 3.3; st4_clear = 4.5; st4_head = 8.5;   // autofilettanti 4 mm
st3_pilot = 2.5; st3_clear = 3.4; st3_head = 6.5;   // autofilettanti 3 mm

// ---------------- Telaio ----------------
D        = 220;          // profondita'
H        = base_h + NU * U;   // altezza utile
ring_h   = 16;           // altezza cornici
ring_r   = 9;            // raggio angoli cornici
side_t   = 3;            // spessore pannelli laterali
side_trim = 3;           // i pannelli laterali sono 3 mm piu' corti sopra e sotto (piu' margine sul piatto)
handle_y = [45, D - 45]; // fori maniglie/piedini (sui lati)
pins     = [[3.5, 3.5], [post - 3.5, 3.5]];   // perni del giunto tra i due tratti di montante
screw_pl = [[post / 2, post / 2]];             // un foro pilota centrale alle estremita' dei montanti
pilot_len = 11;                               // profondita' fori pilota (non tocca i fori dei pannelli a 14 mm)
// viti cornice -> montanti: solo sul lato interno di ogni montante, lontano dai bordi arrotondati
post_end  = 12;                               // blocco pieno in cima e in fondo ai montanti (qui entra la vite centrale)
ring_screws = [[EAR, EAR], [PW - EAR, EAR], [EAR, D - EAR], [PW - EAR, D - EAR]];   // al centro di ogni montante

// ---------------- Componenti (misure tipiche: verificare sui pezzi reali) ----------------
disp_pcb   = [77.2, 42.7];  disp_holes = [67.1, 37.2];  disp_win = [60.5, 43];  disp_win_dx = 0;   // misurate sul pezzo vero (13/11)
disp_pocket = 1;           // TFT: incavo dietro grande come il circuito, cosi' restano 3 mm = spessore del vetro
tol        = 0.3;          // gioco per lato sulle aperture della plancia (la stampa restringe i fori)
oled_pcb   = [27.3, 27.8];  oled_holes = [23.4, 23.8];  oled_win = [23, 12.5]; oled_win_dz = -1.5;   // oled_win: vecchia finestra (non piu' usata)
// 16/11: OLED come il TFT, il vetro esce a filo del frontale. Misure tipiche dei moduli 0,96": DA VERIFICARE col calibro
oled_glass   = [26.7, 19.3];   // vetro (larghezza, altezza)
oled_glass_dz = 0;             // spostamento verticale del vetro rispetto al centro del circuito (+ = verso i pin)
oled_glass_t = 1.7;            // spessore vetro + biadesivo: davanti resta questo, il resto e' incavo per il circuito
oled_pin_row = 1.6;            // distanza della fila di pin dal bordo alto del circuito
oled_pins    = 4;              // pin GND VCC SCL SDA: le saldature sporgono sul lato del vetro -> scanalatura
// 16/11 (misurate): OLED di pve2 e pve3. Vetro 25 x 17, vetro spesso 1,9, circuito 1,2. pve1 resta con i valori sopra.
oled2_glass   = [25, 17];
oled2_glass_t = 1.9;
oled2_solder_front = 0.4;      // davanti alla scanalatura delle saldature restano 0,4 mm (prima 0,6)
oled2_solder_h = 4.5;          // altezza scanalatura (prima 3)
joy_pcb    = [34, 26];      joy_holes  = [26.5, 20.5];  joy_hole_d = 26;  joy_post_h = 16;   // torrette alte 16 mm
pir_pcb    = [32.3, 24.3];  pir_holes  = [28, 0];       pir_dome_d = 23.6;  pir_win = 23.3;   // apertura quadrata per la lente
bar_win    = [10.6, 26.1];  bar_body = [10.2, 25.4, 8];
led_d      = 5.3;
esp_pcb    = [28.6, 56];
sw_body    = [158 + 1, 100 + 1, 25];   // TP-Link TL-SG608E 158 x 100 x 25 + 0.5 mm di gioco per lato
sw_wall = 6; sw_wall_h = 3 + 25 + 0.5; sw_hook = 5; sw_bar_w = 20;   // sponde, fermi e barra dello switch
m2_pilot = 1.8;  m25_pilot = 2.2;

// =====================================================================
//  Utilita'
// =====================================================================
module hex_pattern(w, h, cell = 9, wall = 2.2) {
  dx = cell + wall; dy = (cell + wall) * sqrt(3) / 2;
  intersection() {
    square([w, h]);
    for (j = [0 : ceil(h / dy)]) for (i = [0 : ceil(w / dx)])
      translate([i * dx + (j % 2) * dx / 2, j * dy]) circle(d = cell / cos(30), $fn = 6);
  }
}

module standoff(d = 5.5, h = 4, pilot = m2_pilot) {
  rotate([-90, 0, 0]) difference() { cylinder(d = d, h = h); translate([0, 0, -0.1]) cylinder(d = pilot, h = h + 0.2); }
}

module standoffs4(cx, cz, sp, y0, h = 4, pilot = m2_pilot) {
  for (sx = [-1, 1], sz = [-1, 1]) translate([cx + sx * sp[0] / 2, y0, cz + sz * sp[1] / 2]) standoff(h = h, pilot = pilot);
}

module ear_holes(nu, y0, th) {
  for (u = [0 : nu - 1], hz = U_HOLES, x = [EAR, PW - EAR])
    translate([x, y0 - 1, u * U + hz]) rotate([-90, 0, 0]) cylinder(d = screw_d, h = th + 2);
}

module engrave(txt, x, z, size = 6, y = -4) {
  translate([x, y - 0.01, z]) rotate([90, 0, 0]) mirror([0, 0, 1])
    linear_extrude(0.8) text(txt, size = size, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");
}

module rrect(w, d, r) { translate([r, r]) offset(r = r) square([w - 2 * r, d - 2 * r]); }

module cs_hole(d, head, len) {   // foro con svasatura verso +Z (in cima)
  translate([0, 0, -0.1]) cylinder(d = d, h = len + 0.2);
  translate([0, 0, len - (head - d) / 2]) cylinder(d1 = d, d2 = head, h = (head - d) / 2 + 0.1);
}

// =====================================================================
//  Montanti: fori M6 lungo Y con sede dado sul retro
// =====================================================================
module post_seg(nu, top = "pin", bottom = "pilot", base = 0, eb = 0, et = 0) {
  L = eb + base + nu * U + et;
  difference() {
    union() {
      linear_extrude(L) hull() {                       // spigoli anteriori arrotondati
        for (x = [3, post - 3]) translate([x, 3]) circle(r = 3);
        translate([0, post - 1]) square([post, 1]);
      }
      if (top == "pin") for (p = pins) translate([p[0], p[1], L]) cylinder(d = 4, h = 6);
    }
    for (z = m6_z(nu, base)) translate([EAR, 0, eb + z]) {
      translate([0, -1, 0]) rotate([-90, 0, 0]) cylinder(d = screw_d, h = post + 2);
      translate([0, post - nut_h, 0]) rotate([-90, 0, 0]) rotate([0, 0, 30]) cylinder(d = nut_d, h = nut_h + 1, $fn = 6);
    }
    // fori pilota per i pannelli laterali, su entrambi i fianchi (montante uguale a dx e sx)
    for (z = side_z(nu, base), x = [-0.1, post - 7]) translate([x, 5, eb + z]) rotate([0, 90, 0]) cylinder(d = st3_pilot, h = 7.1);
    // estremita'
    if (bottom == "pilot")  for (p = screw_pl) translate([p[0], p[1], -0.1]) cylinder(d = st4_pilot, h = pilot_len);
    if (bottom == "socket") for (p = pins) translate([p[0], p[1], -0.1]) cylinder(d = 4.4, h = 6.6);
    if (top == "pilot")     for (p = screw_pl) translate([p[0], p[1], L - pilot_len]) cylinder(d = st4_pilot, h = pilot_len + 0.1);
  }
}

module post_corners() {
  for (c = [[0, 0], [PW - post, 0], [0, D - post], [PW - post, D - post]]) translate([c[0], c[1], 0]) children();
}

// =====================================================================
//  Cornici sopra / sotto
// =====================================================================
module ring_body(chamfer_top = true) {
  difference() {
    hull() {
      linear_extrude(ring_h - 3) rrect(PW, D, ring_r);
      translate([0, 0, ring_h - 3]) linear_extrude(3) offset(delta = -1.5) rrect(PW, D, ring_r);
    }
    translate([post, post, -1]) cube([PW - 2 * post, D - 2 * post, ring_h + 2]);
  }
}

// fascia frontale delle cornici (copre i blocchi pieni dei montanti, a filo con le linguette dei ripiani)
// tra i due montanti, sul bordo frontale della cornice, affondata 4 mm dentro la cornice (pezzo unico)
skirt_t = 4; skirt_in = 4;
module skirt() { translate([post, 0, 0]) cube([PW - 2 * post, skirt_t, post_end + skirt_in]); }

module ring_top() {
  difference() {
    union() {
      ring_body();
      translate([0, 0, -post_end]) skirt();                         // fascia frontale: chiude la fessura sopra la plancia
      translate([post - 0.01, post - 0.01, ring_h - 3]) difference() {     // piano a nido d'ape
        cube([PW - 2 * post + 0.02, D - 2 * post + 0.02, 3]);
        translate([6, 6, -1]) linear_extrude(5) hex_pattern(PW - 2 * post - 12, D - 2 * post - 12);
      }
    }
    for (p = ring_screws) translate([p[0], p[1], 0]) cs_hole(st4_clear, st4_head, ring_h);   // viti dall'alto nei montanti
    for (x = [EAR, PW - EAR], y = handle_y) translate([x, y, ring_h - 12]) cylinder(d = st4_pilot, h = 12.2);   // maniglie
    // scritta sul fronte e fasce a nido d'ape ai lati
    translate([PW / 2, -0.01, ring_h / 2 - 1]) rotate([90, 0, 0]) mirror([0, 0, 1])
      linear_extrude(1) text("CLUSTER PROXMOX", size = 7, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");
    for (x0 = [16, PW - 16 - 60]) translate([x0, 1.2, 3]) rotate([90, 0, 0]) linear_extrude(1.4) hex_pattern(60, 8.5, 3.6, 1.3);
  }
}

module ring_bottom() {
  difference() {
    union() {
      ring_body();
      translate([0, 0, ring_h - skirt_in]) skirt();                            // fascia frontale: chiude la fessura sotto il primo vano
      translate([post - 0.01, post - 0.01, 0]) difference() {           // fondo
        cube([PW - 2 * post + 0.02, D - 2 * post + 0.02, 3]);
        translate([30, 30, -1]) linear_extrude(5) hex_pattern(PW - 2 * post - 60, D - 2 * post - 60, 12, 6);
      }
    }
    // viti dal basso nei montanti (svasatura sotto)
    for (p = ring_screws) translate([p[0], p[1], ring_h]) mirror([0, 0, 1]) cs_hole(st4_clear, st4_head, ring_h);
    for (x = [EAR, PW - EAR], y = handle_y) translate([x, y, -0.1]) cylinder(d = st4_pilot, h = 12.2);   // piedini
  }
}

// =====================================================================
//  Pannelli laterali, maniglie, piedini
// =====================================================================
// pannello nel piano XY: X = profondita', Y = altezza, svasature in alto (lato esterno)
module side_panel(nu, base = 0, eb = 0, et = 0, trim = 0) {
  L = eb + base + nu * U + et - 2 * trim;
  difference() {
    linear_extrude(side_t) rrect(D, L, 3);
    translate([16, 10, -1]) linear_extrude(side_t + 2) hex_pattern(D - 36, L - 20, 11, 2.6);
    for (z = side_z(nu, base), y = [5, D - post + 5]) translate([y, eb + z - trim, 0]) cs_hole(st3_clear, st3_head, side_t);
  }
}

// maniglia: profilo ad arco estruso 14 mm (si stampa sdraiata, senza supporti)
module handle() {
  span = handle_y[1] - handle_y[0];
  rotate([90, 0, 90]) difference() {
    translate([0, 0, -7]) linear_extrude(14) {
      for (y = [0, span]) hull() { translate([y - 9, 0]) square([18, 1]); translate([y, 28]) circle(d = 14); }
      hull() { translate([0, 28]) circle(d = 14); translate([span, 28]) circle(d = 14); }
    }
  }
}
module handle_holes() {
  span = handle_y[1] - handle_y[0];
  for (y = [0, span]) translate([0, y, 0]) {
    translate([0, 0, -0.1]) cylinder(d = st4_clear, h = 40);
    translate([0, 0, 8]) cylinder(d = 9, h = 40);   // sede testa vite dall'alto
  }
}
module handle_part() { difference() { handle(); handle_holes(); } }

module foot() {
  difference() {
    cylinder(d1 = 20, d2 = 24, h = 8, $fn = 60);
    translate([0, 0, -0.1]) cylinder(d = st4_clear, h = 8.3);
    translate([0, 0, -0.1]) cylinder(d = 9, h = 4.1);   // sede testa vite dal basso
  }
}

// =====================================================================
//  Ripiani (vassoi nascosti) e pannelli frontali (pezzi separati)
//  Ogni vano: ripiano avvitato ai 4 montanti + pannello frontale avvitato davanti.
//  La linguetta anteriore del ripiano resta coperta dal pannello frontale.
// =====================================================================
ear_t     = 3;                  // linguette dei ripiani, appoggiate davanti ai montanti
ear_w     = post + 4;           // larghezza linguette: inglobano tutta la sponda del ripiano
lip_h     = 5;                  // bordo frontale dei ripiani PC (trave + battuta del PC), sotto l'apertura dei frontali
ctrl_fy   = -2.1;               // ripiano plancia: il bordo frontale resta dietro il pannello inclinato
face_t    = 4;                  // spessore pannelli frontali
fy        = -ear_t;             // retro dei pannelli frontali
tray_x0   = post + 1;  tray_x1 = PW - post - 1;
tray_back = D - post - ear_t;   // il fondo arriva alle linguette posteriori
pc_x      = tray_x0 + 3;        // il PC appoggia alla sponda sinistra

// Frontali dei PC: [larghezza PC, apertura L x H, quota apertura] (misure da verificare col righello)
HP   = [177, [173, 31], 6];     // HP EliteDesk 800 G2 DM (frontale 177 x 34 mm)
MINI = [120, [116, 41], 5.5];   // (vecchio mini PC cinese, non piu' usato)
TECLAST = [114, [110, 39], 5.5];   // pve1 = Teclast N30 114 x 106 x 43.5 mm (troppo alto per 1U: va nel vano da 51 mm)
oled_cx = 216;   // 2 mm a sinistra: lontano dalla linguetta destra del ripiano

function face_holes(h) = abs(h - round(h / U) * U) < 0.01
  ? [for (u = [0 : round(h / U) - 1], hz = U_HOLES) u * U + hz] : [6.35, h - 6.35];

// ---------------- Ripiano ----------------
sw_x = 127;  sw_y = tray_back - sw_body[1];  sw_bar_y = sw_y + sw_body[1] / 2;
module shelf(h, kind = "pc", pcw = 177) {
  esp_b = [70 + 0.8, 63.3 + 0.8];                      // basetta ESP32 70 x 63.3 mm (misurata 14/11) + gioco
  esp_x = tray_x0 + 3 + 1;                                              // tutta a sinistra (a destra va la breadboard)
  esp_y = ctrl_fy + ((sw_y - 3) - ctrl_fy - (esp_b[1] + 3.2)) / 2;      // centrata tra bordo davanti e battuta dello switch
  esp_hole_c = 1 + 1.5 / 2;   // fori basetta: diametro 1.5, bordo del foro a 1 mm dai lati -> centro a 1.75 mm
  esp_pilot  = 1.2;           // foro cieco profondo 2.4 mm per vite autofilettante M1.4 (o M1.2)
  difference() {
    union() {
      difference() {                                                         // fondo
        translate([tray_x0, kind == "pc" ? -ear_t : ctrl_fy, 0.4])                          // fondo: da alette davanti ad alette dietro
          cube([tray_x1 - tray_x0, tray_back + ear_t - (kind == "pc" ? -ear_t : ctrl_fy), 3]);
        if (kind == "pc") difference() {
          translate([tray_x0 + 12, 22, -1]) linear_extrude(6) hex_pattern(tray_x1 - tray_x0 - 24, tray_back - 40);
          translate([pc_x + pcw - 5, 0, -2]) cube([14, tray_back, 10]);              // fascia piena sotto la guida
        }
        else translate([sw_x - 70, sw_y + 8, -1]) linear_extrude(6) hex_pattern(140, sw_body[1] - 16);
      }
      for (x = [tray_x0, tray_x1 - 3]) translate([x, -ear_t, 0.4]) cube([3, tray_back + 2 * ear_t, 10]);   // sponde: entrano nelle linguette
      for (x0 = [0, PW - ear_w], y0 = [-ear_t, tray_back]) translate([x0, y0, 0.4]) cube([ear_w, ear_t, 14]);   // linguette
      if (kind == "pc") translate([0, -ear_t, 0.4]) cube([PW, ear_t, lip_h]);                // bordo frontale continuo da linguetta a linguetta
      if (kind == "pc") translate([pc_x + pcw + 0.8, 12, 0.4]) cube([3, tray_back - 40, 8]);           // guida destra del PC
      if (kind == "control") {
        for (sx = [-1, 1]) translate([sw_x + sx * (sw_body[0] / 2 + sw_wall / 2) - sw_wall / 2, sw_y, 0.4]) cube([sw_wall, sw_body[1], sw_wall_h]);   // sponde alte
        translate([sw_x - sw_body[0] / 2 - sw_wall, sw_y - 3, 0.4]) cube([sw_body[0] + 2 * sw_wall, 3, 8]);                       // battuta davanti
        for (sx = [-1, 1]) translate([sx > 0 ? sw_x + sw_body[0] / 2 - sw_hook : sw_x - sw_body[0] / 2 - 1, tray_back - 0.01, 0.4])
          cube([sw_hook + 1, ear_t + 0.01, 12]);   // si sovrappone 1 mm alla sponda: pezzo unico                                                                                   // fermi dietro agli angoli
        translate([esp_x, esp_y, 0.4]) difference() {                          // alloggiamento basetta ESP32
          cube([esp_b[0] + 3.2, esp_b[1] + 3.2, 3 + 4]);
          translate([1.6, 1.6, 3]) cube([esp_b[0], esp_b[1], 10]);
          translate([(esp_b[0] + 3.2) / 2 - 15, esp_b[1] + 1, 3]) cube([30, 4, 10]);   // uscita cavi verso il retro
        }
      }
    }
    for (x = [EAR, PW - EAR], y0 = [-ear_t - 1, tray_back - 1]) translate([x, y0, 6.35]) rotate([-90, 0, 0]) cylinder(d = screw_d, h = ear_t + 2);
    if (kind == "control") for (sx = [-1, 1]) translate([sw_x + sx * (sw_body[0] / 2 + sw_wall / 2), sw_bar_y, 0.4 + sw_wall_h - 12]) cylinder(d = st3_pilot, h = 12.1);
    if (kind == "control") for (fx = [esp_hole_c, 70 - esp_hole_c], fy = [esp_hole_c, 63.3 - esp_hole_c])   // fori ciechi per le viti della basetta ESP32
      translate([esp_x + 1.6 + 0.4 + fx, esp_y + 1.6 + 0.4 + fy, 1.0]) cylinder(d = esp_pilot, h = 3, $fn = 16);
  }
}

// barra che blocca lo switch dall'alto: 2 viti 3 x 10 svasate nelle sponde del ripiano plancia
module switch_bar() {
  L = sw_body[0] + 2 * sw_wall;
  difference() {
    union() {
      translate([0, -sw_bar_w / 2, 0]) linear_extrude(4) rrect(L, sw_bar_w, 3);
      translate([L / 2 - 50, -sw_bar_w / 2 + 3, -0.8]) cube([100, sw_bar_w - 6, 0.81]);    // pattino: preme leggermente sullo switch
    }
    for (x = [sw_wall / 2, L - sw_wall / 2]) translate([x, 0, 0]) cs_hole(st3_clear, st3_head, 4);
  }
}

// ---------------- Pannello frontale piatto ----------------
module faceplate(h) { translate([0, fy, 0.4]) rotate([90, 0, 0]) linear_extrude(face_t) rrect(PW, h - 0.8, r_face); }
// distanziale pieno sul retro dei frontali: riempie i 3 mm tra frontale e montante dove NON c'e' l'aletta del ripiano
ear_top = 0.4 + 14;                 // l'aletta del ripiano finisce qui (z del vano)
module face_spacers(h, w = post + 2, y_face = fy) {
  intersection() {   // stessi angoli arrotondati del frontale: niente spigoli vivi che sporgono dietro
  translate([0, 0.1, 0.4]) rotate([90, 0, 0]) linear_extrude(-y_face + 1) rrect(PW, h - 0.8, r_face);
  difference() {
    for (x0 = [0, PW - w]) translate([x0, y_face - 0.5, ear_top + 0.2]) cube([w, -y_face + 0.5, h - 0.4 - ear_top - 0.2]);
    for (z = face_holes(h), x = [EAR, PW - EAR]) translate([x, y_face - 2, z]) rotate([-90, 0, 0]) cylinder(d = screw_d, h = -y_face + 3);
  }  }
}
module face_screw_holes(h) {
  for (z = face_holes(h), x = [EAR, PW - EAR]) translate([x, fy - face_t - 1, z]) rotate([-90, 0, 0]) cylinder(d = screw_d, h = face_t + 2);
}

// OLED (16/11): come il TFT. Il circuito entra in un incavo sul retro, il vetro passa nella finestra e arriva a filo davanti.
module oled_cuts(cz, glass = oled_glass, glass_t = oled_glass_t, sfront = 0.6, sh = 3, sw_extra = 2) {
  front = fy - face_t;                 // faccia davanti
  pk = face_t - glass_t;               // profondita' incavo dal retro
  floor0 = fy - pk;                    // fondo dell'incavo
  top = cz + oled_pcb[1] / 2;          // bordo alto del circuito (lato pin)
  // finestra del vetro, passante
  translate([oled_cx - glass[0] / 2 - tol, front - 1, cz + oled_glass_dz - glass[1] / 2 - tol])
    cube([glass[0] + 2 * tol, face_t + 2, glass[1] + 2 * tol]);
  // incavo grande come il circuito
  translate([oled_cx - oled_pcb[0] / 2 - tol, floor0, cz - oled_pcb[1] / 2 - tol])
    cube([oled_pcb[0] + 2 * tol, pk + 1, oled_pcb[1] + 2 * tol]);
  // scanalatura per le saldature dei pin (davanti restano sfront mm)
  gw = oled_pins * 2.54 + sw_extra;
  translate([oled_cx - gw / 2, front + sfront, top - oled_pin_row - sh / 2]) cube([gw, floor0 - front - sfront + 0.01, sh]);
  // fori ciechi M2 dal fondo dell'incavo (davanti restano 0,6 mm)
  for (sx = [-1, 1], sz = [-1, 1]) translate([oled_cx + sx * oled_holes[0] / 2, front + 0.6, cz + sz * oled_holes[1] / 2])
    rotate([-90, 0, 0]) cylinder(d = m2_pilot, h = floor0 - front);
}

module face_pc(h, pc, txt) {
  pcw = pc[0]; ow = pc[1][0]; oh = pc[1][1]; oz = pc[2];
  ox = pc_x + (pcw - ow) / 2;
  difference() {
    union() {
      faceplate(h);
      face_spacers(h);
    }
    face_screw_holes(h);
    translate([ox, fy + 1, oz]) rotate([90, 0, 0]) linear_extrude(face_t + 2) rrect(ow, oh, 3);       // apertura frontale PC
    if (pc == TECLAST) oled_cuts(h / 2);                                          // pve1: schermino suo
    else oled_cuts(h / 2, oled2_glass, oled2_glass_t, oled2_solder_front, oled2_solder_h, 4);   // pve2, pve3

    engrave(txt, oled_cx, h / 2 - oled_pcb[1] / 2 - 4.2, 4.5, fy - face_t);
  }
}

// ---------------- Plancia comandi 2U inclinata (pannello frontale) ----------------
cp_nu = 2; cp_ph = cp_nu * U - 0.8; cp_cz = cp_nu * U / 2;
disp_cx = 82;
bar_cx  = disp_cx + disp_pcb[0] / 2 + 9;      // barra in piedi subito a destra del display
joy_cx  = 162;
pir_cx  = 212;  pir_cz = cp_cz;          // centrato come il joystick
face_x0 = ear_w + 0.3;  face_x1 = PW - face_x0;   // la parte inclinata resta fuori da montanti e alette del ripiano

module tilted() { translate([0, 0, 0.4]) rotate([-tilt, 0, 0]) translate([0, 0, -0.4]) children(); }

module face_solid() {
  translate([face_x0, 0, 0.4]) rotate([90, 0, 0]) linear_extrude(4) square([face_x1 - face_x0, cp_ph - 2]);
  standoffs4(joy_cx, cp_cz, joy_holes, 0, joy_post_h, m25_pilot);   // TFT: niente torrette, il circuito appoggia nell'incavo
  for (sx = [-1, 1]) translate([pir_cx + sx * pir_holes[0] / 2, 0, pir_cz]) standoff(h = 1, pilot = m2_pilot);   // PIR: torrette basse 1 mm
  bw = bar_win[0] + 2 * tol; bh = bar_win[1] + 2 * tol;   // tasca della barra: stessa misura della finestra
  translate([bar_cx - bw / 2 - 2, 0, cp_cz - bh / 2 - 2])
    difference() { cube([bw + 4, bar_body[2] + 1, bh + 4]); translate([2, -1, 2]) cube([bw, bar_body[2] + 3, bh]); }
}

module face_cuts() {
  translate([disp_cx + disp_win_dx - disp_win[0] / 2 - tol, -5, cp_cz - disp_win[1] / 2 - tol]) cube([disp_win[0] + 2 * tol, 6, disp_win[1] + 2 * tol]);
  translate([disp_cx - disp_pcb[0] / 2 - tol, -disp_pocket, cp_cz - disp_pcb[1] / 2 - tol]) cube([disp_pcb[0] + 2 * tol, disp_pocket + 1, disp_pcb[1] + 2 * tol]);   // incavo 1 mm
  for (sx = [-1, 1], sz = [-1, 1]) translate([disp_cx + sx * disp_holes[0] / 2, -4 + 0.6, cp_cz + sz * disp_holes[1] / 2]) rotate([-90, 0, 0]) cylinder(d = m25_pilot, h = 4);   // fori ciechi: davanti restano 0,6 mm
  translate([bar_cx - bar_win[0] / 2 - tol, -5, cp_cz - bar_win[1] / 2 - tol]) cube([bar_win[0] + 2 * tol, 6, bar_win[1] + 2 * tol]);
  translate([joy_cx, -5, cp_cz]) rotate([-90, 0, 0]) cylinder(d = joy_hole_d, h = 6);
  translate([pir_cx - pir_win / 2 - tol, -5, pir_cz - pir_win / 2 - tol]) cube([pir_win + 2 * tol, 6, pir_win + 2 * tol]);
  engrave("STATO CLUSTER", disp_cx, cp_cz + disp_pcb[1] / 2 + 6, 5);
  for (sx = [-1, 1]) translate([pir_cx + sx * pir_holes[0] / 2, -4 + 0.6, pir_cz]) rotate([-90, 0, 0]) cylinder(d = m2_pilot, h = 4.5);   // foro PIR anche nella plancia (cieco, 0,6 mm davanti)
  engrave("PIR", pir_cx, pir_cz - pir_dome_d / 2 - 5, 3.5);
}

module face_control() {   // si stampa in piedi, come e' disegnata
  translate([0, fy, 0]) difference() {
    union() {
      for (x0 = [0, PW - post]) translate([x0, 0, 0.4]) rotate([90, 0, 0]) linear_extrude(4) rrect(post, cp_ph, r_face);   // orecchie dritte
      tilted() face_solid();
      for (x0 = [face_x0, face_x1 - 4]) hull() {                       // guance: solo davanti, fuori dai montanti
        translate([x0, -4, 0.4]) cube([4, 4, cp_ph]);
        tilted() translate([x0, -4, 0.4]) cube([4, 4, cp_ph - 2]);
      }
      for (x0 = [post - r_face - 1, face_x1 - 4]) translate([x0, -4, 0.4]) cube([face_x0 + 4 - post + r_face + 1, 4, cp_ph]);   // unione orecchie-guance (copre anche l'angolo arrotondato interno: niente tacca in alto)
      translate([0, -fy, 0]) face_spacers(cp_nu * U, post, fy);   // distanziali sopra l'aletta del ripiano
    }
    tilted() face_cuts();
    ear_holes(cp_nu, -4, 4);
  }
}

// =====================================================================
//  Montaggio
// =====================================================================
c_frame = "#141a26"; c_post = "#1b2230"; c_panel = "#26314a"; c_shelf = "#3a4766"; c_side = "#2c3a58"; c_acc = "#22d3ee"; c_handle = "#0f141d";
z0 = ring_h;
zr = z0 + post_end;   // inizio della zona a U

module assembly() {
  color(c_frame) ring_bottom();
  color(c_frame) translate([0, 0, z0 + H + 2 * post_end]) ring_top();
  post_corners() {
    color(c_post) translate([0, 0, z0]) post_seg(NU, "pilot", "pilot", base_h, post_end, post_end);   // montante intero
  }
  color(c_side, 0.85) {   // pannelli laterali interi
    translate([-side_t, 0, z0 + side_trim]) rotate([90, 0, 90]) translate([0, 0, side_t]) mirror([0, 0, 1]) side_panel(NU, base_h, post_end, post_end, side_trim);
    translate([PW, 0, z0 + side_trim]) rotate([90, 0, 90]) side_panel(NU, base_h, post_end, post_end, side_trim);
  }
  for (x = [EAR, PW - EAR]) color(c_handle) translate([x, handle_y[0], z0 + H + 2 * post_end + ring_h]) handle_part();
  for (x = [EAR, PW - EAR], y = handle_y) color(c_handle) translate([x, y, -8]) foot();
  // vani
  translate([0, 0, zr]) { color(c_shelf) shelf(base_h, "pc", TECLAST[0]); color(c_panel) face_pc(base_h, TECLAST, "pve1"); }
  translate([0, 0, zr + base_h]) { color(c_shelf) shelf(U, "pc", HP[0]); color(c_panel) face_pc(U, HP, "pve2"); }
  translate([0, 0, zr + base_h + U]) { color(c_shelf) shelf(U, "pc", HP[0]); color(c_panel) face_pc(U, HP, "pve3"); }
  translate([0, 0, zr + base_h + 2 * U]) { color(c_shelf) shelf(2 * U, "control"); color(c_panel) face_control(); }
  // segnaposto (non da stampare)
  if (show_pcs) color("#9aa4b2") translate([pc_x, 0.5, zr + 3.6]) cube([114, 106, 43.5]);
  if (show_pcs) for (z = [base_h, base_h + U]) color("#9aa4b2") translate([pc_x, 0.5, zr + z + 3.6]) cube([177, 175, 34]);
  translate([0, 0, zr + base_h + 2 * U]) {
    color("#7c8794", 0.8) translate([sw_x - 79, sw_y + 0.5, 3.45]) cube([158, 100, 25]);
    color(c_handle) translate([sw_x - sw_body[0] / 2 - sw_wall, sw_bar_y, 0.4 + sw_wall_h]) switch_bar();
    color("#0b1220") translate([0, fy, 0.4]) rotate([-tilt, 0, 0]) translate([82 - 2.5 - 25, -4.3, cp_cz - 19.4]) cube([50, 0.3, 38]);
    color(c_acc) translate([0, fy, 0.4]) rotate([-tilt, 0, 0]) translate([bar_cx - 5, -4.3, cp_cz - 13.1]) cube([10, 0.3, 25.4]);
  }
}

// ---------------- Esportazione pezzi (orientati per la stampa) ----------------
if (part == "post") rotate([-90, 0, 0]) post_seg(NU, "pilot", "pilot", base_h, post_end, post_end);
else if (part == "ring_bottom") ring_bottom();
else if (part == "ring_top") translate([0, D, ring_h]) rotate([180, 0, 0]) ring_top();
else if (part == "side_dx") side_panel(NU, base_h, post_end, post_end, side_trim);
else if (part == "side_sx") mirror([1, 0, 0]) side_panel(NU, base_h, post_end, post_end, side_trim);
else if (part == "handle") rotate([0, 90, 0]) handle_part();
else if (part == "foot") foot();
else if (part == "shelf_hp") shelf(U, "pc", HP[0]);
else if (part == "shelf_base") shelf(base_h, "pc", TECLAST[0]);
else if (part == "shelf_control") shelf(2 * U, "control");
else if (part == "face_hp") rotate([90, 0, 0]) face_pc(U, HP, label);           // faccia in giu'
else if (part == "face_base") rotate([90, 0, 0]) face_pc(base_h, TECLAST, label);
else if (part == "switch_bar") switch_bar();
else if (part == "face_control") face_control();                                  // in piedi
else if (part != "none") assembly();

echo(str("Rack: ", PW + 2 * side_t, " x ", D, " x ", H + 2 * ring_h + 2 * post_end, " mm (", NU, "U + base ", base_h, " mm, senza maniglie e piedini)"));
