const Predictions = () => {
  return (
    <div className="px-4 py-6 sm:px-0">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Risk Predictions</h2>

      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Analyze Trial Risk</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">NCT ID</label>
              <input
                type="text"
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm px-3 py-2 border"
                placeholder="NCT01234567"
              />
            </div>
            <button className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700">
              Analyze Risk
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Predictions
