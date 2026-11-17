// Viste per il manuale di montaggio (le richiama script/crea_immagini_istruzioni.py)
//   step  = numero del passaggio (vedi lo script)
//   scena = "passo" (rack intero) | "pezzo" (un pezzo per l'elenco) | "copertina" | dettagli vari
// Colori: grigio chiaro = gia' montato, blu = pezzo di questo passaggio, rosso = viti/dadi, nero = elettronica
include <rack10.scad>
part = "none";          // non disegnare il montaggio di rack10.scad
step = 1;
scena = "passo";
pezzo = "";
$fn = 40;

c_old = "#c9ced6"; c_new = "#1f7ae0"; c_scr = "#d62828"; c_guide = "#9aa3ad"; c_arrow = "#f08c00";
c_pc = "#2b2f36"; c_pcb_red = "#c0262d"; c_pcb_blu = "#1d4f91"; c_pcb_grn = "#1f6b3a"; c_glass = "#111418";
c_white = "#f2f2ee"; c_black = "#2a2d33";   // colori reali di stampa (copertina e pezzi)

zt   = z0 + H + 2 * post_end;     // base della cornice sopra
bays = [[0, base_h], [base_h, U], [base_h + U, U], [base_h + 2 * U, 2 * U]];   // pve1, pve2, pve3, plancia

// ---------- aiuti grafici ----------
function rot_of(d) = d == "z+" ? [0, 0, 0] : d == "z-" ? [180, 0, 0] : d == "y+" ? [-90, 0, 0] : d == "y-" ? [90, 0, 0] : d == "x+" ? [0, 90, 0] : [0, -90, 0];
function vec_of(d) = d == "z+" ? [0, 0, 1] : d == "z-" ? [0, 0, -1] : d == "y+" ? [0, 1, 0] : d == "y-" ? [0, -1, 0] : d == "x+" ? [1, 0, 0] : [-1, 0, 0];

// vite che entra lungo d con la punta in p, spostata indietro di "fuori" mm, con la linea guida fino al foro
module vite(p, d, l = 20, dia = 4, fuori = 0, svasata = false) {
  v = vec_of(d);
  translate(p - v * fuori) rotate(rot_of(d)) {
    color(c_scr) {
      translate([0, 0, -l]) cylinder(d = dia, h = l, $fn = 16);
      if (svasata) translate([0, 0, -l - dia * 0.6]) cylinder(d1 = dia * 2, d2 = dia, h = dia * 0.6, $fn = 24);
      else translate([0, 0, -l - dia * 0.7]) cylinder(d = dia * 1.9, h = dia * 0.7, $fn = 24);
    }
    if (fuori > 0) color(c_guide) cylinder(d = 0.9, h = fuori, $fn = 8);
  }
}
module dado(p, d = "y+", s = 10, h = 5) { color(c_scr) translate(p) rotate(rot_of(d)) difference() { cylinder(d = s / cos(30), h = h, $fn = 6); translate([0, 0, -1]) cylinder(d = 6, h = h + 2, $fn = 16); } }
// freccia: parte da p e va lungo d per l mm
module freccia(p, d, l = 40, s = 1) {
  color(c_arrow) translate(p) rotate(rot_of(d)) { cylinder(d = 3.2 * s, h = l - 9 * s, $fn = 16); translate([0, 0, l - 9 * s]) cylinder(d1 = 9 * s, d2 = 0, h = 9 * s, $fn = 24); }
}
module nuovo(on) { color(on ? c_new : c_old) children(); }

// ---------- pezzi nella posizione di montaggio ----------
module p_ring_bottom() ring_bottom();
module p_feet() for (x = [EAR, PW - EAR], y = handle_y) translate([x, y, -8]) foot();
module p_posts() post_corners() translate([0, 0, z0]) post_seg(NU, "pilot", "pilot", base_h, post_end, post_end);
module p_side_sx() translate([-side_t, 0, z0 + side_trim]) rotate([90, 0, 90]) translate([0, 0, side_t]) mirror([0, 0, 1]) side_panel(NU, base_h, post_end, post_end, side_trim);
module p_side_dx() translate([PW, 0, z0 + side_trim]) rotate([90, 0, 90]) side_panel(NU, base_h, post_end, post_end, side_trim);
module p_shelf(b) translate([0, 0, zr + bays[b][0]]) if (b == 0) shelf(base_h, "pc", TECLAST[0]); else if (b < 3) shelf(U, "pc", HP[0]); else shelf(2 * U, "control");
module p_ring_top() translate([0, 0, zt]) ring_top();
module p_handles() for (x = [EAR, PW - EAR]) translate([x, handle_y[0], zt + ring_h]) handle_part();
module p_face(b) translate([0, 0, zr + bays[b][0]])
  if (b == 0) face_pc(base_h, TECLAST, "pve1"); else if (b == 1) face_pc(U, HP, "pve2"); else if (b == 2) face_pc(U, HP, "pve3"); else face_control();
module p_switch() { zb = zr + base_h + 2 * U; color("#4a5160") translate([sw_x - 79, sw_y + 0.5, zb + 3.45]) cube([158, 100, 25]);
  for (i = [0 : 7]) color("#15181d") translate([sw_x - 70 + i * 17, sw_y + 100.4, zb + 8]) cube([14, 0.4, 12]); }
module p_switch_bar() translate([sw_x - sw_body[0] / 2 - sw_wall, sw_bar_y, zr + base_h + 2 * U + 0.4 + sw_wall_h]) switch_bar();
esp_b = [77.8, 63.8]; esp_x = tray_x1 - 3 - 1 - esp_b[0] - 3.2; esp_y = 22;
module p_esp() translate([esp_x + 1.6, esp_y + 1.6, zr + base_h + 2 * U + 3.6]) {
  color(c_pcb_blu) cube([77, 63, 1.6]);
  color("#111") translate([24, 3.5, 1.6]) cube([28.6, 56, 1.6]);
  color("#bfc5cc") translate([30, 18, 3.2]) cube([16, 18, 3]);
}
module p_pcs() {
  color(c_pc) translate([pc_x, 0.5, zr + 3.6]) cube([114, 106, 43.5]);
  for (b = [1 : 2]) color(c_pc) translate([pc_x, 0.5, zr + bays[b][0] + 3.6]) cube([177, 175, 34]);
}

// elettronica della plancia, nelle coordinate di face_control()
module e_tft()   { color(c_pcb_red) translate([disp_cx - disp_pcb[0] / 2, -1, cp_cz - disp_pcb[1] / 2]) cube([disp_pcb[0], 1.6, disp_pcb[1]]);
                   color(c_glass) translate([disp_cx - 30, -4, cp_cz - 21.5]) cube([60, 3, 43]); }
module e_bar()   color("#1c1f24") translate([bar_cx - bar_body[0] / 2, -4, cp_cz - bar_body[1] / 2]) cube([bar_body[0], bar_body[2], bar_body[1]]);
module e_joy()   { color(c_black) translate([joy_cx - joy_pcb[0] / 2, joy_post_h, cp_cz - joy_pcb[1] / 2]) cube([joy_pcb[0], 1.6, joy_pcb[1]]);
                   color("#3a3d44") translate([joy_cx - 10, 2, cp_cz - 10]) cube([20, joy_post_h - 2, 20]);
                   color("#26282c") translate([joy_cx, 2, cp_cz]) rotate([90, 0, 0]) { cylinder(d = 6, h = 10); translate([0, 0, 10]) cylinder(d = 24, h = 8); } }
module e_pir()   { color(c_pcb_grn) translate([pir_cx - pir_pcb[0] / 2, 1, pir_cz - pir_pcb[1] / 2]) cube([pir_pcb[0], 1.6, pir_pcb[1]]);
                   color("#f4f4f0") translate([pir_cx - 11.5, -4, pir_cz - 11.5]) cube([23, 5, 23]);
                   color("#f4f4f0") translate([pir_cx, -4, pir_cz]) scale([1, 0.7, 1]) sphere(d = 22); }
module plancia_frame() translate([0, fy, 0]) tilted() children();   // stesso riferimento di face_control()
// OLED, nelle coordinate di face_pc(h)
module e_oled(h) { color(c_pcb_blu) translate([oled_cx - oled_pcb[0] / 2, fy + 3.5, h / 2 - oled_pcb[1] / 2]) cube([oled_pcb[0], 1.6, oled_pcb[1]]);
                   color(c_glass) translate([oled_cx - 13, fy + 1, h / 2 - 9]) cube([26, 2.5, 15]); }

// =====================================================================
//  Scene
// =====================================================================
module passo(s) {
  // ---- 1: piedini (vista da sotto) ----
  if (s == 1) { nuovo(false) p_ring_bottom();
    color(c_new) translate([0, 0, -45]) p_feet();
    for (x = [EAR, PW - EAR], y = handle_y) vite([x, y, 4], "z+", 12, 4, 90);
  }
  // ---- 2: montanti ----
  if (s == 2) { nuovo(false) { p_ring_bottom(); p_feet(); }
    color(c_new) translate([0, 0, 70]) p_posts();
    for (p = ring_screws) vite([p[0], p[1], ring_h + 8], "z+", 25, 4, 70, true);
    for (p = ring_screws) freccia([p[0], p[1], z0 + 330], "z-", 50);
  }
  if (s == 21) { nuovo(false) { p_ring_bottom(); p_feet(); } color(c_new) p_posts();     // dettaglio: viti da sotto
    for (p = ring_screws) vite([p[0], p[1], ring_h + 8], "z+", 25, 4, 70, true);
  }
  // ---- 3 e 4: pannelli laterali ----
  if (s == 3 || s == 4) { nuovo(false) { p_ring_bottom(); p_feet(); p_posts(); if (s == 4) p_side_dx(); }
    sx = s == 3 ? 1 : -1;
    color(c_new) translate([sx * 60, 0, 0]) if (s == 3) p_side_dx(); else p_side_sx();
    for (z = side_z(NU, base_h), y = [5, D - post + 5])
      vite([s == 3 ? PW + side_t : -side_t, y, z0 + post_end + z], s == 3 ? "x-" : "x+", 12, 3, 110, true);
  }
  // ---- 5: dadi (vista da dietro) ----
  if (s == 5) { nuovo(false) { p_ring_bottom(); p_feet(); p_posts(); p_side_dx(); p_side_sx(); }
    mz = m6_z(NU, base_h);
    for (x = [EAR, PW - EAR]) {
      for (i = [0, 2, 3, 5, 6, 8, 9, 11, 12, 14]) dado([x, post - 5.4 + 40, zr + mz[i]], "y-");
      for (i = [0, 3, 6, 9]) dado([x, D - 5.4 + 40, zr + mz[i]], "y-");
    }
  }
  if (s == 51) {   // dettaglio: un montante con i dadi
    color(c_old) post_seg(NU, "pilot", "pilot", base_h, post_end, post_end);
    mz = m6_z(NU, base_h);
    for (i = [0, 2, 3, 5, 6, 8, 9, 11, 12, 14]) dado([EAR, post + 25, post_end + mz[i]], "y-");
    for (i = [0, 2, 3]) freccia([EAR + 22, post + 25, post_end + mz[i]], "y-", 22, 0.6);
  }
  // ---- 6, 7, 8: ripiani ----
  if (s >= 6 && s <= 8) {
    nuovo(false) { p_ring_bottom(); p_feet(); p_posts(); p_side_dx(); p_side_sx(); for (b = [0 : 3]) if ((s == 7 && b == 0) || (s == 8 && b < 3)) p_shelf(b); }
    nb = s == 6 ? [0] : s == 7 ? [1, 2] : [3];
    for (b = nb) color(c_new) translate([0, 0, s == 6 ? 300 : s == 7 ? (b == 1 ? 330 : 200) : 120]) p_shelf(b);
    for (b = nb, x = [EAR, PW - EAR]) vite([x, tray_back, zr + bays[b][0] + 6.35], "y+", 25, 6, 45);
    freccia([PW / 2, D / 2, zt + 60], "z-", 60);
  }
  // ---- 9: switch, barra, ESP32 (dettaglio sul solo ripiano) ----
  if (s == 9) { zb = zr + base_h + 2 * U;
    translate([0, 0, -zb]) {
      color(c_old) p_shelf(3);
      translate([0, 0, 70]) p_switch();
      color(c_new) translate([0, 0, 120]) p_switch_bar();
      for (sx = [-1, 1]) vite([sw_x + sx * (sw_body[0] / 2 + sw_wall / 2), sw_bar_y, zb + 0.4 + sw_wall_h + 4], "z-", 12, 3, 140, true);
      translate([0, 0, 45]) p_esp();
    }
  }
  // ---- 10: cornice sopra ----
  if (s == 10) { nuovo(false) { p_ring_bottom(); p_feet(); p_posts(); p_side_dx(); p_side_sx(); for (b = [0 : 3]) p_shelf(b); p_switch(); p_switch_bar(); p_esp(); }
    color(c_new) translate([0, 0, 70]) p_ring_top();
    for (p = ring_screws) vite([p[0], p[1], zt + ring_h - 8], "z-", 25, 4, 130, true);
  }
  // ---- 11: maniglie ----
  if (s == 11) { nuovo(false) { p_ring_bottom(); p_feet(); p_posts(); p_side_dx(); p_side_sx(); for (b = [0 : 3]) p_shelf(b); p_ring_top(); }
    color(c_new) translate([0, 0, 50]) p_handles();
    for (x = [EAR, PW - EAR], y = handle_y) vite([x, y, zt + ring_h + 8], "z-", 20, 4, 110);
  }
  // ---- 12: elettronica sul retro della plancia (vista da dietro) ----
  if (s == 12) { color(c_old) face_control();
    plancia_frame() {
      translate([0, 30, 0]) e_tft();
      translate([0, 30, 0]) e_bar();
      translate([0, 30, 0]) e_joy();
      translate([0, 30, 0]) e_pir();
      for (sx = [-1, 1], sz = [-1, 1]) vite([disp_cx + sx * disp_holes[0] / 2, 0.6, cp_cz + sz * disp_holes[1] / 2], "y-", 4, 2.5, 60);
      for (sx = [-1, 1], sz = [-1, 1]) vite([joy_cx + sx * joy_holes[0] / 2, joy_post_h + 1.6, cp_cz + sz * joy_holes[1] / 2], "y-", 8, 2.5, 50);
      for (sx = [-1, 1]) vite([pir_cx + sx * pir_holes[0] / 2, 2.6, pir_cz], "y-", 6, 2, 60);
    }
  }
  if (s == 121) { color(c_old) face_control(); plancia_frame() { e_tft(); e_bar(); e_joy(); e_pir(); } }   // plancia pronta
  // ---- 13: OLED sui frontali (vista da dietro) ----
  if (s == 13) { color(c_old) intersection() { face_pc(U, HP, "pve2"); translate([150, -20, -5]) cube([120, 60, 60]); }   // solo la parte con l'OLED
    translate([0, 30, 0]) e_oled(U);
    for (sx = [-1, 1], sz = [-1, 1]) vite([oled_cx + sx * oled_holes[0] / 2, fy + 5.1, U / 2 + sz * oled_holes[1] / 2], "y-", 6, 2, 55);
  }
  // ---- 14: PC nei vani ----
  if (s == 14) { nuovo(false) { p_ring_bottom(); p_feet(); p_posts(); p_side_dx(); p_side_sx(); for (b = [0 : 3]) p_shelf(b); p_ring_top(); p_handles(); p_switch(); p_switch_bar(); p_esp(); }
    translate([0, -170, 0]) p_pcs();
    for (b = [0 : 2]) freccia([pc_x + 60, -60, zr + bays[b][0] + 20], "y+", 45);
  }
  // ---- 15: frontali e plancia ----
  if (s == 15) { nuovo(false) { p_ring_bottom(); p_feet(); p_posts(); p_side_dx(); p_side_sx(); for (b = [0 : 3]) p_shelf(b); p_ring_top(); p_handles(); p_switch(); p_switch_bar(); p_esp(); p_pcs(); }
    color(c_new) translate([0, -60, 0]) for (b = [0 : 3]) p_face(b);
    translate([0, -60, 0]) translate([0, 0, zr + bays[3][0]]) plancia_frame() { e_tft(); e_bar(); e_joy(); e_pir(); }
    for (b = [0 : 3], z = (b == 3 ? [for (u = [0 : 1], hz = U_HOLES) u * U + hz] : face_holes(bays[b][1])), x = [EAR, PW - EAR])
      vite([x, fy - face_t, zr + bays[b][0] + z], "y+", 30, 6, 110);
  }
}

module montato(colori_veri = true) {   // rack finito
  cw = colori_veri ? c_white : c_old; cb = colori_veri ? c_black : c_old;
  color(cw) { p_ring_bottom(); p_feet(); p_ring_top(); p_handles(); }
  color(cb) { p_posts(); p_side_dx(); p_side_sx(); for (b = [0 : 3]) p_shelf(b); for (b = [0 : 3]) p_face(b); p_switch_bar(); }
  p_switch(); p_esp(); p_pcs();
  translate([0, 0, zr + bays[3][0]]) plancia_frame() { e_tft(); e_bar(); e_joy(); e_pir(); }
  for (b = [0 : 2]) translate([0, 0, zr + bays[b][0]]) e_oled(bays[b][1]);
}

// pezzi singoli per l'elenco (colore reale di stampa)
module pezzo_singolo(n) {
  if (n == "01") color(c_black) post_seg(NU, "pilot", "pilot", base_h, post_end, post_end);
  if (n == "03") color(c_white) ring_bottom();
  if (n == "04") color(c_white) ring_top();
  if (n == "05") color(c_black) side_panel(NU, base_h, post_end, post_end, side_trim);
  if (n == "06") color(c_black) mirror([1, 0, 0]) side_panel(NU, base_h, post_end, post_end, side_trim);
  if (n == "09") color(c_white) handle_part();
  if (n == "10") color(c_white) foot();
  if (n == "11") color(c_black) shelf(U, "pc", HP[0]);
  if (n == "12") color(c_black) shelf(base_h, "pc", TECLAST[0]);
  if (n == "13") color(c_black) shelf(2 * U, "control");
  if (n == "14") color(c_black) face_pc(base_h, TECLAST, "pve1");
  if (n == "15") color(c_black) face_pc(U, HP, "pve2");
  if (n == "16") color(c_black) face_pc(U, HP, "pve3");
  if (n == "17") color(c_black) face_control();
  if (n == "18") color(c_black) switch_bar();
}

if (scena == "passo") passo(step);
if (scena == "copertina") montato(true);
if (scena == "pezzo") pezzo_singolo(pezzo);
