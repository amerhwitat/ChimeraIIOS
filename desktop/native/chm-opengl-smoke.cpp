#include <GLFW/glfw3.h>
#include <cstdio>
#include <cstring>

static void draw_frame(int width, int height) {
    glViewport(0, 0, width, height);
    glClearColor(0.035f, 0.09f, 0.16f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    glOrtho(-1.0, 1.0, -1.0, 1.0, -1.0, 1.0);
    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
    glBegin(GL_TRIANGLES);
    glColor3f(0.12f, 0.58f, 0.95f); glVertex2f(-0.85f, -0.72f);
    glColor3f(0.18f, 0.88f, 0.72f); glVertex2f(0.85f, -0.72f);
    glColor3f(0.48f, 0.38f, 0.95f); glVertex2f(0.0f, 0.82f);
    glEnd();
}
int main(int argc, char** argv) {
    const bool self_test = argc > 1 && std::strcmp(argv[1], "--self-test") == 0;
    if (!glfwInit()) { std::fprintf(stderr, "GLFW initialization failed\n"); return 2; }
    glfwWindowHint(GLFW_VISIBLE, self_test ? GLFW_FALSE : GLFW_TRUE);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 2);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 1);
    GLFWwindow* window = glfwCreateWindow(640, 400, "Chimera OpenGL", nullptr, nullptr);
    if (!window) { glfwTerminate(); std::fprintf(stderr, "OpenGL context creation failed\n"); return 3; }
    glfwMakeContextCurrent(window);
    const char* version = reinterpret_cast<const char*>(glGetString(GL_VERSION));
    const char* renderer = reinterpret_cast<const char*>(glGetString(GL_RENDERER));
    if (!version || !renderer) { glfwDestroyWindow(window); glfwTerminate(); return 4; }
    std::printf("OpenGL version: %s\nRenderer: %s\n", version, renderer);
    int width = 0, height = 0;
    glfwGetFramebufferSize(window, &width, &height);
    while (glGetError() != GL_NO_ERROR) {}
    draw_frame(width, height);
    glfwSwapBuffers(window);
    const GLenum error = glGetError();
    if (error != GL_NO_ERROR) {
        std::fprintf(stderr, "OpenGL render failed with error 0x%x\n", error);
        glfwDestroyWindow(window); glfwTerminate(); return 5;
    }
    if (!self_test) {
        while (!glfwWindowShouldClose(window)) {
            glfwPollEvents();
            glfwGetFramebufferSize(window, &width, &height);
            draw_frame(width, height);
            glfwSwapBuffers(window);
        }
    }
    glfwDestroyWindow(window);
    glfwTerminate();
    return 0;
}
