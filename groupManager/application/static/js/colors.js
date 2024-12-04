function replaceClass(before, after) {
    // Ищем все элементы с классом before
    const elements = document.querySelectorAll(`.${before}`);
    
    // Перебираем найденные элементы
    elements.forEach(element => {
        console.log(element);
        if (element.hasAttribute('color_const')) {
            return; // Пропускаем этот элемент
        }

        // Меняем класс before на after
        element.classList.remove(before);
        element.classList.add(after);
    });
}
