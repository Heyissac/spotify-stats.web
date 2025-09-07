// Efecto parallax suave en las partículas
document.addEventListener('mousemove', (e) => {
    const particles = document.querySelectorAll('.particle');
    const x = e.clientX / window.innerWidth;
    const y = e.clientY / window.innerHeight;

    particles.forEach((particle, index) => {
        const speed = (index + 1) * 0.5;
        const xOffset = (x - 0.5) * speed * 20;
        const yOffset = (y - 0.5) * speed * 20;

        particle.style.transform = `translate(${xOffset}px, ${yOffset}px)`;
    });
});

// Animación de entrada escalonada para las features
window.addEventListener('load', () => {
    const features = document.querySelectorAll('.glassmorphism-light');
    features.forEach((feature, index) => {
        setTimeout(() => {
            feature.classList.add('opacity-100', 'translate-y-0');
        }, index * 200);
    });
});