 #version 330
in vec2 vert;
void main() {
    gl_Position = vec4(vert, 0.0, 1.0);
}