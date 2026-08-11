import { useCounterStore } from "@/store/benchmark.store"

function App() {
  const count = useCounterStore((state) => state.count)
  const increment = useCounterStore((state) => state.increment)

  return (
    <div className="App">
      <header className="App-header">
        <p className="text-red-600">
          Pagina principal de la aplicacion, se puede ver el contador y un boton para incrementar el contador.
        </p>

        <button
          className="bg-blue-500 px-4 py-2 text-white rounded"
          onClick={increment}
        >
          Count is {count}
        </button>
      </header>
    </div>
  )
}

export default App