// Controlli geometrici dei fori. Ogni test deve dare un oggetto VUOTO.
//  test = "ring_top_out"    : svasature cornice sopra che escono dal pezzo
//  test = "ring_bottom_out" : svasature cornice sotto che escono dal pezzo
//  test = "post_clash"      : fori pilota montante che toccano altri fori
//  test = "align"           : viti cornice NON allineate ai fori pilota dei montanti
include <rack10.scad>
part = "none";
test = "ring_top_out";

module ring_envelope() {   // sagoma piena della cornice (senza apertura centrale)
  hull() {
    linear_extrude(ring_h - 3) rrect(PW, D, ring_r);
    translate([0, 0, ring_h - 3]) linear_extrude(3) offset(delta = -2.5) rrect(PW, D, ring_r);
  }
}
module ring_top_holes() { for (p = ring_screws) translate([p[0], p[1], 0]) cs_hole(st4_clear, st4_head, ring_h); }
module ring_bottom_holes() { for (p = ring_screws) translate([p[0], p[1], ring_h]) mirror([0, 0, 1]) cs_hole(st4_clear, st4_head, ring_h); }
module top_material() { union() { ring_body(); translate([post, post, ring_h - 3]) cube([PW - 2 * post, D - 2 * post, 3]); } }
module bottom_material() { union() { ring_body(); translate([post, post, 0]) cube([PW - 2 * post, D - 2 * post, 3]); } }

module post_other_holes(nu, base) {
  for (z = m6_z(nu, base)) translate([EAR, 0, z]) {
    translate([0, -1, 0]) rotate([-90, 0, 0]) cylinder(d = screw_d, h = post + 2);
    translate([0, post - nut_h, 0]) rotate([-90, 0, 0]) rotate([0, 0, 30]) cylinder(d = nut_d, h = nut_h + 1, $fn = 6);
  }
  for (z = side_z(nu, base), x = [-0.1, post - 7]) translate([x, 5, z]) rotate([0, 90, 0]) cylinder(d = st3_pilot, h = 7.1);
  for (p = pins) translate([p[0], p[1], -0.1]) cylinder(d = 4.4, h = 6.6);
}
module post_pilots(L) {
  for (p = screw_pl) { translate([p[0], p[1], -0.1]) cylinder(d = st4_pilot, h = pilot_len); translate([p[0], p[1], L - pilot_len]) cylinder(d = st4_pilot, h = pilot_len + 0.1); }
}

// interseca le colonne delle viti cornice con i montanti "pieni" meno i fori pilota: se resta qualcosa, non sono allineate
module align_test() {
  intersection() {
    for (p = ring_screws) translate([p[0], p[1], -1]) cylinder(d = st4_pilot - 0.2, h = 3);
    difference() {
      post_corners() translate([0, 0, -5]) cube([post, post, 10]);
      post_corners() for (p = screw_pl) translate([p[0], p[1], -6]) cylinder(d = st4_pilot, h = 12);
    }
  }
}

if (test == "ring_top_out") difference() { ring_top_holes(); top_material(); translate([post, post, -1]) cube([PW - 2 * post, D - 2 * post, ring_h - 3 + 1]); }
else if (test == "ring_bottom_out") difference() { ring_bottom_holes(); bottom_material(); translate([post, post, 3]) cube([PW - 2 * post, D - 2 * post, ring_h]); }
else if (test == "post_clash") {
  intersection() { post_pilots(base_h + 2 * U); post_other_holes(2, base_h); }
  translate([40, 0, 0]) intersection() { post_pilots(2 * U); post_other_holes(2, 0); }
}
else if (test == "align") align_test();
